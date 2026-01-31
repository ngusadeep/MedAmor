#!/usr/bin/env python3
"""Command-line interface for platform management."""

import argparse
import getpass
import sys

from .app import create_app
from .database import db
from .models import User


def create_user_interactive():
    """Create a user interactively via command line."""
    print("Create New User")
    print("-" * 40)

    username = input("Username: ").strip()
    if not username:
        print("Error: Username is required")
        sys.exit(1)

    email = input("Email: ").strip()
    if not email:
        print("Error: Email is required")
        sys.exit(1)

    first_name = input("First Name (optional): ").strip() or None
    last_name = input("Last Name (optional): ").strip() or None

    is_admin_input = input("Is Admin? (y/N): ").strip().lower()
    is_admin = is_admin_input in ("y", "yes", "true", "1")

    password = getpass.getpass("Password: ")
    if not password:
        print("Error: Password is required")
        sys.exit(1)

    password_confirm = getpass.getpass("Confirm Password: ")
    if password != password_confirm:
        print("Error: Passwords do not match")
        sys.exit(1)

    return {
        "username": username,
        "email": email,
        "first_name": first_name,
        "last_name": last_name,
        "is_admin": is_admin,
        "password": password,
    }


def cmd_create_user(args):
    """Handle the create-user command."""
    app = create_app()

    with app.app_context():
        # Get user data interactively or from args
        if args.username and args.email:
            if args.password:
                password = args.password
            else:
                password = getpass.getpass("Password: ")
                password_confirm = getpass.getpass("Confirm Password: ")
                if password != password_confirm:
                    print("Error: Passwords do not match")
                    sys.exit(1)

            user_data = {
                "username": args.username,
                "email": args.email,
                "first_name": args.first_name,
                "last_name": args.last_name,
                "is_admin": args.admin,
                "password": password,
            }
        else:
            user_data = create_user_interactive()

        # Check for existing user
        if User.query.filter_by(username=user_data["username"]).first():
            print(f"Error: User with username '{user_data['username']}' already exists")
            sys.exit(1)
        if User.query.filter_by(email=user_data["email"]).first():
            print(f"Error: User with email '{user_data['email']}' already exists")
            sys.exit(1)

        # Create user
        user = User(
            username=user_data["username"],
            email=user_data["email"],
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            is_admin=user_data["is_admin"],
        )
        user.set_password(user_data["password"])

        db.session.add(user)
        db.session.commit()

        print(f"\nUser '{user.username}' created successfully!")
        print(f"  ID: {user.id}")
        print(f"  Email: {user.email}")
        print(f"  Admin: {user.is_admin}")


def cmd_list_users(args):
    """Handle the list-users command."""
    app = create_app()

    with app.app_context():
        users = User.query.all()
        if not users:
            print("No users found.")
            return

        print(f"{'ID':<5} {'Username':<20} {'Email':<30} {'Admin':<6} {'Active':<6}")
        print("-" * 70)
        for user in users:
            print(
                f"{user.id:<5} {user.username:<20} {user.email:<30} "
                f"{'Yes' if user.is_admin else 'No':<6} {'Yes' if user.is_active else 'No':<6}"
            )


def cmd_init_db(args):
    """Initialize the database tables."""
    app = create_app()

    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Platform CLI - Manage users and database"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # create-user command
    create_user_parser = subparsers.add_parser("create-user", help="Create a new user")
    create_user_parser.add_argument("--username", "-u", help="Username")
    create_user_parser.add_argument("--email", "-e", help="Email address")
    create_user_parser.add_argument("--password", "-p", help="Password (not recommended, use prompt)")
    create_user_parser.add_argument("--first-name", "-f", dest="first_name", help="First name")
    create_user_parser.add_argument("--last-name", "-l", dest="last_name", help="Last name")
    create_user_parser.add_argument("--admin", "-a", action="store_true", help="Make user an admin")
    create_user_parser.set_defaults(func=cmd_create_user)

    # list-users command
    list_users_parser = subparsers.add_parser("list-users", help="List all users")
    list_users_parser.set_defaults(func=cmd_list_users)

    # init-db command
    init_db_parser = subparsers.add_parser("init-db", help="Initialize database tables")
    init_db_parser.set_defaults(func=cmd_init_db)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
