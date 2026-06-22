"use client"

import DocumentTree from "@/components/DocumentTree";
import { useState, useEffect } from "react";
import SideBar from "@/components/SideBar";
import ReenqueueModal from "@/components/modals/RenenqueueModal";
import { getDocuments, getDocumentInfo, setTaskToPending } from "@/api/documents";

export default function Viewer() {
  const [documentsData, setDocumentsData] = useState([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const PAGE_SIZE = 50;
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [docTree, setDocTree] = useState({});
  const [docStats, setDocStats] = useState({});
  const [reenqueueModalOpen, setReenqueueModalOpen] = useState(false);
  const [reenqueueTask, setReenqueueTask] = useState({});

  function documentSelectionCallback(docId){
    if (docId){
      setSelectedDocument(docId);
    }
  }

  function reenqueueConfirmationCallback(task){
    setReenqueueTask(task);
    setReenqueueModalOpen(true);
  }

  function reenqueueAllPagesCallback(task){
    // TODO: implement re-enqueue for all pages
  }

  async function confirmReenqueue(){
    try{
      await setTaskToPending(reenqueueTask.id);
      setReenqueueModalOpen(false);
    }
    catch(error){
      console.error("could not set task to pending ", error);
    }
  }

  useEffect(() => {
    const fetchDocuments = async () => {
      const result = await getDocuments(currentPage, PAGE_SIZE);
      setDocumentsData(result.documents);
      setTotalPages(Math.ceil(result.total / PAGE_SIZE));
    };

    fetchDocuments();
  }, [currentPage]);

  useEffect(() => {
    const fetchDocumentData = async () => {
      try {
        if (selectedDocument){
          const newDocInfo = await getDocumentInfo(selectedDocument);
          setDocTree(newDocInfo?.docTree);
          setDocStats(newDocInfo?.docStats);
        }
      } catch (err) {
        console.error("Failed to fetch document data:", err);
      }
    };

    fetchDocumentData();

    // Auto-refresh every 5 seconds
    const intervalId = setInterval(fetchDocumentData, 5000);

    return () => clearInterval(intervalId);
  }, [selectedDocument]);

  return (
    <>
    <div className="flex-1 flex w-full px-1 py-1 bg-white dark:bg-black overflow-auto">
          <SideBar
            allDocumentsData={documentsData}
            documentSelectionCallback={documentSelectionCallback}
            currentPage={currentPage}
            totalPages={totalPages}
            onPageChange={setCurrentPage}
          />
          <div className="flex flex-col h-full w-full bg-gray-800 rounded-lg p-5">
            <h1>Digitization Viewer</h1>
              <div className="flex-row h-full flex w-full gap-3 rounded-lg bg-gray-700">
                <DocumentTree
                  docTree={docTree}
                  docStats={docStats}
                  reenqueueConfirmationCallback={reenqueueConfirmationCallback}
                  reenqueueAllPagesCallback={reenqueueAllPagesCallback}
                />
              </div>
          </div>
      </div>
      {reenqueueModalOpen && (
        <ReenqueueModal
          taskName={`${reenqueueTask.taskName} | Index ${reenqueueTask.pageIndex}`}
          onConfirm={confirmReenqueue}
          onCancel={() => setReenqueueModalOpen(false)}
        />
      )}
    </>
  );
}
