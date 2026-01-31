#!/usr/bin/env python3
"""
Interactive FHIR Patient Browser

Connects to a FHIR server and provides an interactive interface to browse patients
and view their complete medical timelines.

Controls:
    Up/Down arrows: Select patient
    Left/Right arrows: Navigate pages
    Enter: View selected patient's timeline
    q: Quit (or go back from timeline view)
    r: Refresh patient list
"""

import curses
import json
import os
import re
import requests
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple

import sys
from pathlib import Path

# Add parent directory to path for importing fhir_reader
sys.path.insert(0, str(Path(__file__).parent.parent))

from fhir_reader.timeline import FHIRTimelineConverter
from fhir_reader.resources import EXPORT_PROFILES

# ============================================================================
# CONFIGURATION
# ============================================================================

FHIR_SERVER_URL = "http://localhost:9080/fhir"

# Number of patients to show per page
PATIENTS_PER_PAGE = 10

# ============================================================================
# FHIR Client
# ============================================================================


class FHIRClient:
    """Simple FHIR client for patient operations."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/fhir+json",
            "Content-Type": "application/fhir+json",
        })

    def get_patients(self, count: int = 50, offset: int = 0) -> Tuple[List[Dict], int]:
        """
        Fetch patients from the server.

        Returns:
            Tuple of (list of patient resources, total count)
        """
        try:
            # Use _count and _offset for pagination
            params = {
                "_count": count,
                "_offset": offset,
                "_sort": "family",  # Sort by family name
            }
            response = self.session.get(f"{self.base_url}/Patient", params=params)
            response.raise_for_status()
            bundle = response.json()

            patients = []
            if "entry" in bundle:
                for entry in bundle["entry"]:
                    if entry.get("resource", {}).get("resourceType") == "Patient":
                        patients.append(entry["resource"])

            # Get total count
            total = bundle.get("total", len(patients))

            return patients, total

        except requests.RequestException as e:
            raise ConnectionError(f"Failed to fetch patients: {e}")

    def get_patient_everything(self, patient_id: str) -> Dict[str, Any]:
        """
        Fetch all data for a patient using $everything operation.

        Returns:
            FHIR Bundle containing all patient data
        """
        try:
            response = self.session.get(
                f"{self.base_url}/Patient/{patient_id}/$everything",
                params={"_count": 1000},  # Get up to 1000 resources
            )
            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            raise ConnectionError(f"Failed to fetch patient data: {e}")

    def test_connection(self) -> bool:
        """Test if the FHIR server is reachable."""
        try:
            response = self.session.get(f"{self.base_url}/metadata", timeout=5)
            return response.status_code == 200
        except:
            return False


# ============================================================================
# Patient Display Helpers
# ============================================================================


def format_patient_name(patient: Dict) -> str:
    """Extract and format patient name."""
    if "name" not in patient or len(patient["name"]) == 0:
        return "Unknown Name"

    name = patient["name"][0]
    parts = []

    if "prefix" in name:
        parts.extend(name["prefix"])
    if "given" in name:
        parts.extend(name["given"])
    if "family" in name:
        parts.append(name["family"])

    return " ".join(parts) if parts else "Unknown Name"


def format_patient_info(patient: Dict) -> str:
    """Format patient info for list display."""
    name = format_patient_name(patient)
    gender = patient.get("gender", "?")[0].upper()
    dob = patient.get("birthDate", "Unknown DOB")
    patient_id = patient.get("id", "?")

    return f"{name} | {gender} | DOB: {dob} | ID: {patient_id}"


def sanitize_filename(name: str) -> str:
    """Sanitize a string for use in a filename."""
    # Replace spaces with underscores, remove special characters
    sanitized = re.sub(r'[^\w\s-]', '', name)
    sanitized = re.sub(r'\s+', '_', sanitized)
    return sanitized.lower()


def filter_bundle_by_resource_types(bundle: Dict, resource_types: List[str]) -> Dict:
    """Filter a FHIR bundle to only include specified resource types."""
    if not resource_types:
        return bundle  # Return full bundle if no filter specified

    filtered_bundle = {
        "resourceType": "Bundle",
        "type": bundle.get("type", "searchset"),
        "entry": []
    }

    if "entry" in bundle:
        for entry in bundle["entry"]:
            resource = entry.get("resource", {})
            if resource.get("resourceType") in resource_types:
                filtered_bundle["entry"].append(entry)

    return filtered_bundle


# ============================================================================
# Curses UI
# ============================================================================


class PatientBrowser:
    """Interactive patient browser using curses."""

    def __init__(self, stdscr, fhir_client: FHIRClient):
        self.stdscr = stdscr
        self.client = fhir_client
        self.patients: List[Dict] = []
        self.total_patients = 0
        self.current_page = 0
        self.selected_index = 0
        self.status_message = ""
        self.error_message = ""

        # Setup curses
        curses.curs_set(0)  # Hide cursor
        curses.use_default_colors()
        if curses.has_colors():
            curses.start_color()
            curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)  # Selected
            curses.init_pair(2, curses.COLOR_GREEN, -1)  # Header
            curses.init_pair(3, curses.COLOR_RED, -1)  # Error
            curses.init_pair(4, curses.COLOR_YELLOW, -1)  # Status
            curses.init_pair(5, curses.COLOR_CYAN, -1)  # Info

    def load_patients(self):
        """Load patients for current page."""
        self.error_message = ""
        self.status_message = "Loading patients..."
        self.draw()

        try:
            offset = self.current_page * PATIENTS_PER_PAGE
            self.patients, self.total_patients = self.client.get_patients(
                count=PATIENTS_PER_PAGE,
                offset=offset
            )
            self.status_message = f"Loaded {len(self.patients)} patients"

            # Reset selection if out of bounds
            if self.selected_index >= len(self.patients):
                self.selected_index = max(0, len(self.patients) - 1)

        except Exception as e:
            self.error_message = str(e)
            self.patients = []

    @property
    def total_pages(self) -> int:
        """Calculate total number of pages."""
        if self.total_patients == 0:
            return 1
        return (self.total_patients + PATIENTS_PER_PAGE - 1) // PATIENTS_PER_PAGE

    def draw(self):
        """Draw the main patient list screen."""
        self.stdscr.clear()
        height, width = self.stdscr.getmaxyx()

        # Header
        header = f" FHIR Patient Browser - {FHIR_SERVER_URL} "
        self.stdscr.attron(curses.color_pair(2) | curses.A_BOLD)
        self.stdscr.addstr(0, 0, "=" * width)
        self.stdscr.addstr(1, (width - len(header)) // 2, header)
        self.stdscr.addstr(2, 0, "=" * width)
        self.stdscr.attroff(curses.color_pair(2) | curses.A_BOLD)

        # Controls
        controls = " [↑↓] Select  [←→] Page  [Enter] View  [r] Refresh  [q] Quit "
        self.stdscr.attron(curses.color_pair(5))
        self.stdscr.addstr(3, (width - len(controls)) // 2, controls)
        self.stdscr.attroff(curses.color_pair(5))

        # Page info
        page_info = f" Page {self.current_page + 1}/{self.total_pages} | Total: {self.total_patients} patients "
        self.stdscr.attron(curses.color_pair(4))
        self.stdscr.addstr(4, (width - len(page_info)) // 2, page_info)
        self.stdscr.attroff(curses.color_pair(4))

        self.stdscr.addstr(5, 0, "-" * width)

        # Patient list
        list_start_y = 6
        for i, patient in enumerate(self.patients):
            y = list_start_y + i
            if y >= height - 3:
                break

            info = format_patient_info(patient)
            # Truncate if too long
            if len(info) > width - 4:
                info = info[:width - 7] + "..."

            if i == self.selected_index:
                self.stdscr.attron(curses.color_pair(1))
                self.stdscr.addstr(y, 0, " " * width)
                self.stdscr.addstr(y, 2, f"▶ {info}")
                self.stdscr.attroff(curses.color_pair(1))
            else:
                self.stdscr.addstr(y, 2, f"  {info}")

        # Error message
        if self.error_message:
            self.stdscr.attron(curses.color_pair(3))
            err_msg = f" Error: {self.error_message[:width-10]} "
            self.stdscr.addstr(height - 2, 0, err_msg)
            self.stdscr.attroff(curses.color_pair(3))
        elif self.status_message:
            self.stdscr.attron(curses.color_pair(4))
            self.stdscr.addstr(height - 2, 0, f" {self.status_message} ")
            self.stdscr.attroff(curses.color_pair(4))

        self.stdscr.refresh()

    def view_patient_timeline(self, patient: Dict):
        """Fetch and display patient timeline."""
        patient_id = patient.get("id")
        patient_name = format_patient_name(patient)

        self.stdscr.clear()
        height, width = self.stdscr.getmaxyx()

        # Show loading message
        self.stdscr.attron(curses.color_pair(4))
        msg = f"Loading data for {patient_name}..."
        self.stdscr.addstr(height // 2, (width - len(msg)) // 2, msg)
        self.stdscr.attroff(curses.color_pair(4))
        self.stdscr.refresh()

        try:
            # Fetch patient data
            bundle = self.client.get_patient_everything(patient_id)

            # Convert to timeline
            converter = FHIRTimelineConverter(bundle)
            timeline = converter.convert(include_costs=True, include_codes=False)
            stats = converter.get_summary_stats()

            # Display timeline in scrollable view (pass patient and bundle for export)
            self.display_timeline(patient, bundle, timeline, stats)

        except Exception as e:
            self.stdscr.clear()
            self.stdscr.attron(curses.color_pair(3))
            error_msg = f"Error loading patient: {str(e)}"
            self.stdscr.addstr(height // 2, 2, error_msg[:width - 4])
            self.stdscr.addstr(height // 2 + 2, 2, "Press any key to go back...")
            self.stdscr.attroff(curses.color_pair(3))
            self.stdscr.refresh()
            self.stdscr.getch()

    def display_timeline(self, patient: Dict, bundle: Dict, timeline: str, stats: Dict):
        """Display timeline in a scrollable view."""
        patient_name = format_patient_name(patient)
        lines = timeline.split("\n")
        scroll_pos = 0

        while True:
            self.stdscr.clear()
            height, width = self.stdscr.getmaxyx()

            # Header
            header = f" Timeline: {patient_name} "
            self.stdscr.attron(curses.color_pair(2) | curses.A_BOLD)
            self.stdscr.addstr(0, 0, header[:width])
            self.stdscr.attroff(curses.color_pair(2) | curses.A_BOLD)

            # Stats bar
            stats_str = f" Events: {stats['total_events']} | Encounters: {stats['encounters']} | Meds: {stats['medications']} | Allergies: {stats['allergies']} "
            self.stdscr.attron(curses.color_pair(5))
            self.stdscr.addstr(1, 0, stats_str[:width])
            self.stdscr.attroff(curses.color_pair(5))

            # Controls
            controls = " [↑↓/PgUp/PgDn] Scroll  [Home/End] Jump  [e] Export  [q] Back "
            self.stdscr.attron(curses.color_pair(4))
            self.stdscr.addstr(2, 0, controls[:width])
            self.stdscr.attroff(curses.color_pair(4))

            self.stdscr.addstr(3, 0, "-" * width)

            # Content area
            content_start = 4
            content_height = height - content_start - 1
            visible_lines = lines[scroll_pos:scroll_pos + content_height]

            for i, line in enumerate(visible_lines):
                y = content_start + i
                if y >= height - 1:
                    break
                # Truncate line if too long
                display_line = line[:width - 1] if len(line) >= width else line
                try:
                    self.stdscr.addstr(y, 0, display_line)
                except curses.error:
                    pass  # Ignore errors at screen edge

            # Scroll position indicator
            if len(lines) > content_height:
                scroll_pct = int((scroll_pos / max(1, len(lines) - content_height)) * 100)
                scroll_info = f" Line {scroll_pos + 1}/{len(lines)} ({scroll_pct}%) "
                self.stdscr.addstr(height - 1, width - len(scroll_info) - 1, scroll_info)

            self.stdscr.refresh()

            # Handle input
            key = self.stdscr.getch()

            if key == ord("q") or key == 27:  # q or ESC
                break
            elif key == curses.KEY_UP:
                scroll_pos = max(0, scroll_pos - 1)
            elif key == curses.KEY_DOWN:
                scroll_pos = min(len(lines) - content_height, scroll_pos + 1)
            elif key == curses.KEY_PPAGE:  # Page Up
                scroll_pos = max(0, scroll_pos - content_height)
            elif key == curses.KEY_NPAGE:  # Page Down
                scroll_pos = min(len(lines) - content_height, scroll_pos + content_height)
            elif key == curses.KEY_HOME:
                scroll_pos = 0
            elif key == curses.KEY_END:
                scroll_pos = max(0, len(lines) - content_height)
            elif key == ord("e"):  # Export
                export_type = self.show_export_menu(patient)
                if export_type:
                    filenames = self.export_patient_timeline_from_bundle(patient, bundle, export_type)
                    self.show_export_result(filenames)

    def show_export_menu(self, patient: Dict) -> Optional[str]:
        """Show export menu and return selected option."""
        options = [
            ("1", "full", "Full Content - All FHIR resources"),
            ("2", "handoff_minimal", "Handoff Minimal - Demo handoff resources"),
            ("3", "handoff_complete", "Handoff Complete - Production handoff resources"),
            ("4", "imaging_minimal", "Imaging Minimal - Demo imaging resources"),
            ("5", "imaging_complete", "Imaging Complete - Production imaging resources"),
            ("6", "all", "Export All - Generate all 5 export files"),
        ]

        selected = 0

        while True:
            self.stdscr.clear()
            height, width = self.stdscr.getmaxyx()

            # Header
            patient_name = format_patient_name(patient)
            header = f" Export Timeline: {patient_name} "
            self.stdscr.attron(curses.color_pair(2) | curses.A_BOLD)
            self.stdscr.addstr(0, 0, "=" * width)
            self.stdscr.addstr(1, (width - len(header)) // 2, header)
            self.stdscr.addstr(2, 0, "=" * width)
            self.stdscr.attroff(curses.color_pair(2) | curses.A_BOLD)

            # Instructions
            self.stdscr.attron(curses.color_pair(5))
            self.stdscr.addstr(4, 2, "Select export format:")
            self.stdscr.attroff(curses.color_pair(5))

            # Options
            for i, (key, profile, description) in enumerate(options):
                y = 6 + i
                if i == selected:
                    self.stdscr.attron(curses.color_pair(1))
                    self.stdscr.addstr(y, 0, " " * width)
                    self.stdscr.addstr(y, 2, f"▶ [{key}] {description}")
                    self.stdscr.attroff(curses.color_pair(1))
                else:
                    self.stdscr.addstr(y, 4, f"[{key}] {description}")

            # Controls
            self.stdscr.attron(curses.color_pair(4))
            self.stdscr.addstr(height - 2, 2, "[↑↓] Select  [Enter] Export  [q/Esc] Cancel")
            self.stdscr.attroff(curses.color_pair(4))

            self.stdscr.refresh()

            key = self.stdscr.getch()

            if key == ord("q") or key == 27:  # q or ESC
                return None
            elif key == curses.KEY_UP:
                selected = (selected - 1) % len(options)
            elif key == curses.KEY_DOWN:
                selected = (selected + 1) % len(options)
            elif key == ord("\n") or key == curses.KEY_ENTER:
                return options[selected][1]
            elif ord("1") <= key <= ord("6"):
                idx = key - ord("1")
                return options[idx][1]

    def export_patient_timeline_from_bundle(self, patient: Dict, bundle: Dict, export_type: str) -> List[str]:
        """Export patient timeline to file(s) using pre-fetched bundle. Returns list of created filenames."""
        patient_id = patient.get("id", "unknown")
        patient_name = format_patient_name(patient)
        safe_name = sanitize_filename(patient_name)

        height, width = self.stdscr.getmaxyx()

        try:
            # Determine which exports to generate
            if export_type == "all":
                export_profiles = ["full", "handoff_minimal", "handoff_complete",
                                   "imaging_minimal", "imaging_complete"]
            else:
                export_profiles = [export_type]

            created_files = []

            for profile_key in export_profiles:
                # Update status
                self.stdscr.clear()
                profile_name = EXPORT_PROFILES.get(profile_key, {}).get("name", profile_key)
                msg = f"Generating {profile_name}..."
                self.stdscr.attron(curses.color_pair(4))
                self.stdscr.addstr(height // 2, (width - len(msg)) // 2, msg)
                self.stdscr.attroff(curses.color_pair(4))
                self.stdscr.refresh()

                # Get resource types for this profile
                profile = EXPORT_PROFILES.get(profile_key, {})
                resource_types = profile.get("resource_types")

                # Filter bundle if needed
                if resource_types:
                    filtered_bundle = filter_bundle_by_resource_types(bundle, resource_types)
                else:
                    filtered_bundle = bundle

                # Convert to timeline
                converter = FHIRTimelineConverter(filtered_bundle)
                timeline = converter.convert(include_costs=True, include_codes=False)

                # Generate filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{patient_id}_{safe_name}_{profile_key}_{timestamp}.txt"

                # Write file
                with open(filename, "w") as f:
                    f.write(f"Patient ID: {patient_id}\n")
                    f.write(f"Patient Name: {patient_name}\n")
                    f.write(f"Export Type: {profile_key}\n")
                    f.write(f"Generated: {datetime.now().isoformat()}\n")
                    f.write("\n" + "=" * 80 + "\n\n")
                    f.write(timeline)

                created_files.append(filename)

            return created_files

        except Exception as e:
            self.stdscr.clear()
            self.stdscr.attron(curses.color_pair(3))
            error_msg = f"Error exporting: {str(e)}"
            self.stdscr.addstr(height // 2, 2, error_msg[:width - 4])
            self.stdscr.addstr(height // 2 + 2, 2, "Press any key to continue...")
            self.stdscr.attroff(curses.color_pair(3))
            self.stdscr.refresh()
            self.stdscr.getch()
            return []

    def show_export_result(self, filenames: List[str]):
        """Display the result of an export operation."""
        self.stdscr.clear()
        height, width = self.stdscr.getmaxyx()

        # Header
        self.stdscr.attron(curses.color_pair(2) | curses.A_BOLD)
        self.stdscr.addstr(0, 0, "=" * width)
        header = " Export Complete "
        self.stdscr.addstr(1, (width - len(header)) // 2, header)
        self.stdscr.addstr(2, 0, "=" * width)
        self.stdscr.attroff(curses.color_pair(2) | curses.A_BOLD)

        if filenames:
            self.stdscr.attron(curses.color_pair(5))
            self.stdscr.addstr(4, 2, f"Created {len(filenames)} file(s):")
            self.stdscr.attroff(curses.color_pair(5))

            for i, filename in enumerate(filenames):
                y = 6 + i
                if y >= height - 3:
                    self.stdscr.addstr(y, 4, f"... and {len(filenames) - i} more files")
                    break
                # Truncate filename if too long
                display_name = filename if len(filename) < width - 6 else "..." + filename[-(width - 9):]
                self.stdscr.addstr(y, 4, display_name)
        else:
            self.stdscr.attron(curses.color_pair(3))
            self.stdscr.addstr(4, 2, "No files were created.")
            self.stdscr.attroff(curses.color_pair(3))

        # Instructions
        self.stdscr.attron(curses.color_pair(4))
        self.stdscr.addstr(height - 2, 2, "Press any key to continue...")
        self.stdscr.attroff(curses.color_pair(4))

        self.stdscr.refresh()
        self.stdscr.getch()

    def run(self):
        """Main event loop."""
        # Initial load
        self.load_patients()

        while True:
            self.draw()
            key = self.stdscr.getch()

            if key == ord("q") or key == 27:  # q or ESC to quit
                break

            elif key == curses.KEY_UP:
                if self.selected_index > 0:
                    self.selected_index -= 1

            elif key == curses.KEY_DOWN:
                if self.selected_index < len(self.patients) - 1:
                    self.selected_index += 1

            elif key == curses.KEY_LEFT:
                if self.current_page > 0:
                    self.current_page -= 1
                    self.selected_index = 0
                    self.load_patients()

            elif key == curses.KEY_RIGHT:
                if self.current_page < self.total_pages - 1:
                    self.current_page += 1
                    self.selected_index = 0
                    self.load_patients()

            elif key == ord("r"):  # Refresh
                self.load_patients()

            elif key == ord("\n") or key == curses.KEY_ENTER:  # Enter
                if self.patients and 0 <= self.selected_index < len(self.patients):
                    self.view_patient_timeline(self.patients[self.selected_index])


def main():
    """Entry point for the patient browser."""
    print(f"Connecting to FHIR server: {FHIR_SERVER_URL}")

    # Create client and test connection
    client = FHIRClient(FHIR_SERVER_URL)

    print("Testing connection...")
    if not client.test_connection():
        print(f"Error: Cannot connect to FHIR server at {FHIR_SERVER_URL}")
        print("Make sure the server is running and accessible.")
        return 1

    print("Connection successful! Starting browser...")

    # Run curses application
    def run_browser(stdscr):
        browser = PatientBrowser(stdscr, client)
        browser.run()

    try:
        curses.wrapper(run_browser)
    except KeyboardInterrupt:
        pass

    print("Goodbye!")
    return 0


if __name__ == "__main__":
    exit(main())
