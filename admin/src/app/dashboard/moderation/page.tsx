'use client';

import React, { useState, useEffect } from 'react';

interface Report {
    id: string;
    type: string;
    targetId: string;
    reason: string;
    details?: string;
    status: string;
    createdAt: string;
}

export default function ModerationDashboard() {
    const [reports, setReports] = useState<Report[]>([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState<'pending' | 'reviewed' | 'all'>('pending');

    useEffect(() => {
        fetchReports();
    }, [filter]);

    const fetchReports = async () => {
        try {
            setLoading(true);
            const params = new URLSearchParams();
            if (filter !== 'all') params.append('status', filter);

            const response = await fetch(`/api/reports?${params}`);
            const data = await response.json();
            setReports(data.reports || []);
        } catch (error) {
            console.error('Error fetching reports:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleResolve = async (reportId: string) => {
        if (!confirm('Mark this report as resolved?')) return;

        try {
            await fetch(`/api/reports/${reportId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status: 'resolved' }),
            });
            fetchReports();
        } catch (error) {
            alert('Failed to resolve report');
        }
    };

    const handleDismiss = async (reportId: string) => {
        if (!confirm('Dismiss this report?')) return;

        try {
            await fetch(`/api/reports/${reportId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status: 'dismissed' }),
            });
            fetchReports();
        } catch (error) {
            alert('Failed to dismiss report');
        }
    };

    const getTypeIcon = (type: string) => {
        switch (type) {
            case 'comment':
                return '💬';
            case 'review':
                return '⭐';
            case 'user':
                return '👤';
            case 'drama':
                return '📺';
            default:
                return '🚨';
        }
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'pending':
                return 'bg-yellow-100 text-yellow-800';
            case 'resolved':
                return 'bg-green-100 text-green-800';
            default:
                return 'bg-gray-100 text-gray-800';
        }
    };

    return (
        <div className="container mx-auto p-6">
            <div className="mb-6">
                <h1 className="text-3xl font-bold text-gray-900">Content Moderation</h1>
                <p className="text-gray-600 mt-1">Review reported content</p>
            </div>

            {/* Filters */}
            <div className="flex gap-2 mb-6">
                {(['pending', 'reviewed', 'all'] as const).map((status) => (
                    <button
                        key={status}
                        onClick={() => setFilter(status)}
                        className={`px-4 py-2 rounded-lg font-semibold capitalize transition-colors ${filter === status
                                ? 'bg-orange-500 text-white'
                                : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
                            }`}
                    >
                        {status}
                    </button>
                ))}
            </div>

            {/* Reports List */}
            {loading ? (
                <div className="flex justify-center items-center py-20">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-500"></div>
                </div>
            ) : reports.length === 0 ? (
                <div className="bg-white rounded-lg shadow p-12 text-center">
                    <div className="text-6xl mb-4">✓</div>
                    <p className="text-xl text-gray-600">
                        No {filter !== 'all' ? filter : ''} reports
                    </p>
                </div>
            ) : (
                <div className="space-y-4">
                    {reports.map((report) => (
                        <div key={report.id} className="bg-white rounded-lg shadow hover:shadow-md transition-shadow">
                            <div className="p-6">
                                <div className="flex items-start justify-between mb-4">
                                    <div className="flex items-center gap-3">
                                        <span className="text-3xl">{getTypeIcon(report.type)}</span>
                                        <div>
                                            <h3 className="text-lg font-bold text-gray-900 capitalize">
                                                {report.type} Report
                                            </h3>
                                            <p className="text-sm text-gray-500">
                                                {new Date(report.createdAt).toLocaleDateString()}
                                            </p>
                                        </div>
                                    </div>
                                    <span
                                        className={`px-3 py-1 rounded-full text-xs font-semibold ${getStatusColor(
                                            report.status
                                        )}`}
                                    >
                                        {report.status}
                                    </span>
                                </div>

                                <div className="space-y-2">
                                    <p className="font-semibold text-gray-900">{report.reason}</p>
                                    {report.details && (
                                        <p className="text-gray-600 text-sm">{report.details}</p>
                                    )}

                                    {report.status === 'pending' && (
                                        <div className="flex gap-2 mt-4">
                                            <button
                                                onClick={() => handleResolve(report.id)}
                                                className="px-4 py-2 bg-green-600 text-white rounded-lg font-semibold hover:bg-green-700 transition-colors"
                                            >
                                                Resolve
                                            </button>
                                            <button
                                                onClick={() => handleDismiss(report.id)}
                                                className="px-4 py-2 bg-red-600 text-white rounded-lg font-semibold hover:bg-red-700 transition-colors"
                                            >
                                                Dismiss
                                            </button>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
