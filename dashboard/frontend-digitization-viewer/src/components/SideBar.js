"use client"
// components/SideBar.jsx
import { useState, useEffect } from "react"
import { ChevronLeft, ChevronRight } from "lucide-react";

import DocumentThumbnail from "./DocumentThumbnail";

export default function SideBar({allDocumentsData, documentSelectionCallback, currentPage, totalPages, onPageChange}) {
    const [sideBarOpen, setSideBarOpen] = useState(true);
    const [currentDocument, setCurrentDocument] = useState(null);

    useEffect(() => {
        documentSelectionCallback(currentDocument);
    }, [currentDocument]);

    function docSelected(docId){
        setCurrentDocument(docId);
    }

    return (
        <div className={`flex flex-row gap-1 px-1 h-full`}>
            {sideBarOpen && (
                <div className="flex flex-col p-2 bg-gray-800 rounded-lg w-64 h-full">
                    <>
                    <h3>
                        Documents
                    </h3>
                    <div className="flex flex-col p-2 gap-1 rounded-lg w-full h-full bg-gray-600 overflow-y-auto">
                    {allDocumentsData.map((doc) => (
                        <div key={doc.id}
                             onClick={() => docSelected(doc.id)}
                             className="flex flex-col w-full">
                            <DocumentThumbnail
                                title={doc.title}
                                digitized={doc.digitized}
                                failedTasks={doc.failed_tasks}
                                className={doc.id === currentDocument ? "bg-gray-900" : "bg-gray-700"}
                            />
                        </div>
                    ))}
                    </div>
                    <div className="flex items-center justify-between px-2 py-1 text-xs text-gray-300 gap-2">
                        <button
                            onClick={() => onPageChange(p => Math.max(1, p - 1))}
                            disabled={currentPage === 1}
                            className="px-2 py-1 rounded bg-gray-700 disabled:opacity-40 hover:bg-gray-600"
                        >
                            ‹
                        </button>
                        <span>{currentPage} / {totalPages}</span>
                        <button
                            onClick={() => onPageChange(p => Math.min(totalPages, p + 1))}
                            disabled={currentPage === totalPages}
                            className="px-2 py-1 rounded bg-gray-700 disabled:opacity-40 hover:bg-gray-600"
                        >
                            ›
                        </button>
                    </div>
                    </>
                </div>
            )}
            
            <div className="flex items-center bg-gray-600 rounded-lg h-full" onClick={() => setSideBarOpen(!sideBarOpen)}>
                {sideBarOpen ? <ChevronLeft /> : <ChevronRight />}
            </div>
        </div>
  )
}
