import React from 'react';
import { NextPageContext } from 'next';
import Link from 'next/link';

interface ErrorProps {
  statusCode?: number;
}

export default function ErrorPage({ statusCode }: ErrorProps) {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-slate-50 text-slate-800 p-4">
      <h1 className="text-3xl font-black mb-2 text-slate-900">
        {statusCode ? 'Error ' + statusCode : 'An unexpected error occurred'}
      </h1>
      <p className="text-sm text-slate-500 mb-6">
        {statusCode
          ? 'A server-side error ' + statusCode + ' occurred on the compliance portal.'
          : 'An error occurred on the client interface.'}
      </p>
      <Link
        href="/dashboard"
        className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-lg transition"
      >
        Return to Dashboard
      </Link>
    </div>
  );
}

ErrorPage.getInitialProps = ({ res, err }: NextPageContext) => {
  const statusCode = res ? res.statusCode : err ? err.statusCode : 404;
  return { statusCode };
};