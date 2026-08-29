import Link from 'next/link';

export default function Custom404() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-slate-50 text-slate-800 p-4">
      <h1 className="text-4xl font-black mb-2 text-slate-900">404 - Page Not Found</h1>
      <p className="text-sm text-slate-500 mb-6">The requested statutory verification route does not exist.</p>
      <Link
        href="/dashboard"
        className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-lg transition"
      >
        Return to Dashboard
      </Link>
    </div>
  );
}
