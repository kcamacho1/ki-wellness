"use client";
import { useState } from "react";

export default function DashboardPanel({
  title,
  icon,
  children,
  defaultExpanded = false, // new prop
}: {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
  defaultExpanded?: boolean;
}) {
  const [expanded, setExpanded] = useState(defaultExpanded);

  return (
    <div className="border rounded-lg bg-white shadow p-4">
      {expanded ? (
        <div>
          <div className="flex justify-between items-center mb-2">
            <h2 className="text-xl font-semibold flex items-center gap-2">
              {icon}
              {title}
            </h2>
            <button
              className="text-gray-500 hover:text-black"
              onClick={() => setExpanded(false)}
            >
              ✕ Close
            </button>
          </div>
          <div>{children}</div>
        </div>
      ) : (
        <button
          onClick={() => setExpanded(true)}
          className="w-full flex items-center gap-2 text-left hover:bg-gray-100 p-2 rounded"
        >
          {icon}
          <span className="font-medium">{title}</span>
        </button>
      )}
    </div>
  );
}
