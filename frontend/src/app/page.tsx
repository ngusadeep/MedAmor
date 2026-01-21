"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Activity, Users, Clock, TrendingUp, Plus, Search, FileText, Image, Stethoscope } from "lucide-react";

interface PatientCase {
  id: string;
  patientId: string;
  caseType: string;
  priority: "urgent" | "routine" | "follow_up";
  createdAt: string;
  status: "pending" | "processing" | "completed";
  estimatedTime?: string;
}

export default function Dashboard() {
  const [searchTerm, setSearchTerm] = useState("");

  // Mock data for demonstration
  const mockCases: PatientCase[] = [
    {
      id: "CASE-001",
      patientId: "PT-2024-001",
      caseType: "NSCLC Stage III",
      priority: "urgent",
      createdAt: "2024-01-21T10:00:00Z",
      status: "processing",
      estimatedTime: "2-4 hours"
    },
    {
      id: "CASE-002",
      patientId: "PT-2024-002",
      caseType: "Breast Cancer",
      priority: "routine",
      createdAt: "2024-01-21T09:30:00Z",
      status: "pending",
      estimatedTime: "6-8 hours"
    },
    {
      id: "CASE-003",
      patientId: "PT-2024-003",
      caseType: "Colorectal Cancer",
      priority: "follow_up",
      createdAt: "2024-01-21T08:15:00Z",
      status: "completed",
      estimatedTime: "Completed"
    }
  ];

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "urgent": return "destructive";
      case "routine": return "default";
      case "follow_up": return "secondary";
      default: return "default";
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "pending": return "secondary";
      case "processing": return "default";
      case "completed": return "default";
      default: return "secondary";
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <Stethoscope className="h-8 w-8 text-blue-600 mr-3" />
              <h1 className="text-2xl font-bold text-gray-900">OncoSync</h1>
              <span className="ml-2 text-sm text-gray-500">Virtual Tumor Board</span>
            </div>
            <Button className="flex items-center gap-2">
              <Plus className="h-4 w-4" />
              New Case
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Cases</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">12</div>
              <p className="text-xs text-muted-foreground">
                +2 from yesterday
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Time Saved</CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">156h</div>
              <p className="text-xs text-muted-foreground">
                vs. traditional process
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Guidelines Compliance</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">95%</div>
              <p className="text-xs text-muted-foreground">
                +10% from baseline
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Specialists</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">8</div>
              <p className="text-xs text-muted-foreground">
                Across departments
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Cases Section */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">Patient Cases</h2>
              <div className="flex items-center gap-4">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <Input
                    placeholder="Search cases..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10 w-64"
                  />
                </div>
                <Button variant="outline" size="sm">
                  Filter
                </Button>
              </div>
            </div>
          </div>

          <div className="divide-y divide-gray-200">
            {mockCases.map((case_) => (
              <div key={case_.id} className="px-6 py-4 hover:bg-gray-50">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="flex-shrink-0">
                      <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                        <FileText className="h-5 w-5 text-blue-600" />
                      </div>
                    </div>
                    <div>
                      <h3 className="text-sm font-medium text-gray-900">{case_.id}</h3>
                      <p className="text-sm text-gray-500">Patient: {case_.patientId}</p>
                    </div>
                    <Badge variant={getPriorityColor(case_.priority)}>
                      {case_.priority.toUpperCase()}
                    </Badge>
                    <Badge variant={getStatusColor(case_.status)}>
                      {case_.status.toUpperCase()}
                    </Badge>
                  </div>

                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <p className="text-sm text-gray-500">{case_.caseType}</p>
                      <p className="text-xs text-gray-400">
                        Est. completion: {case_.estimatedTime}
                      </p>
                    </div>
                    <Button variant="outline" size="sm">
                      View Details
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Agent Status Section */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Image className="h-4 w-4" alt="Radiology Agent Icon" />
                Radiology Agent
              </CardTitle>
              <CardDescription>MedGemma-CXR Analysis</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <span className="text-sm text-green-600">Active</span>
                <Badge variant="secondary">Processing</Badge>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <FileText className="h-4 w-4" />
                Pathology Agent
              </CardTitle>
              <CardDescription>Biomarker Extraction</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <span className="text-sm text-green-600">Active</span>
                <Badge variant="secondary">Ready</Badge>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Stethoscope className="h-4 w-4" />
                Treatment Recommender
              </CardTitle>
              <CardDescription>Evidence-based Options</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <span className="text-sm text-green-600">Active</span>
                <Badge variant="secondary">Ready</Badge>
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
