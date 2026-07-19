import React from "react";
import { Button } from "../ui/button";
import { AlertTriangle, Trash2 } from "lucide-react";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription,
} from "../ui/dialog";

const DeleteWorkerDialog = ({ worker, onClose, onDelete }) => {
  return (
    <Dialog open={!!worker} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="bg-[var(--color-surface)] border-[#2A2A2D] max-w-sm">
        <DialogHeader>
          <DialogTitle className="font-['Cormorant_Garamond'] text-2xl flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-red-400" />
            Potvrda brisanja
          </DialogTitle>
          <DialogDescription className="text-[#9CA3AF]">
            Da li ste sigurni da želite trajno da obrišete radnika <span className="text-white font-medium">{worker?.name}</span>? Ova akcija se ne može poništiti.
          </DialogDescription>
        </DialogHeader>
        <div className="flex gap-3 mt-4">
          <Button
            variant="outline"
            onClick={onClose}
            className="flex-1 border-[#2A2A2D] bg-transparent hover:bg-[var(--color-background)]"
            data-testid="cancel-delete-btn"
          >
            Otkaži
          </Button>
          <Button
            onClick={() => onDelete(worker?.id)}
            className="flex-1 bg-red-500 hover:bg-red-600 text-white"
            data-testid="confirm-delete-btn"
          >
            <Trash2 className="w-4 h-4 mr-2" />
            Obriši
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default DeleteWorkerDialog;
