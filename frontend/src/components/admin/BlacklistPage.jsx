import React, { useState, useEffect } from "react";
import { toast } from "sonner";
import axios from "axios";
import { API, useTenant, getTenantHeaders, getToken } from "../../App";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Phone, Ban, Check, Shield, Trash2, Plus } from "lucide-react";
import { format, parseISO } from "date-fns";
import { srLatn as sr } from "date-fns/locale";
import { PhoneInput } from "../PhoneInput";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "../ui/table";

const BlacklistPage = () => {
  const tenant = useTenant();
  const [blacklist, setBlacklist] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newPhone, setNewPhone] = useState("");
  const [isAdding, setIsAdding] = useState(false);

  const token = getToken();
  const headers = { Authorization: `Bearer ${token}`, ...getTenantHeaders(tenant?.tenant_id) };

  useEffect(() => {
    fetchBlacklist();
  }, []);

  const fetchBlacklist = async () => {
    try {
      const response = await axios.get(`${API}/blacklist`, { headers });
      setBlacklist(response.data);
    } catch (error) {
      toast.error("Greška pri učitavanju crne liste");
    } finally {
      setLoading(false);
    }
  };

  const handleAddToBlacklist = async () => {
    if (!newPhone.trim()) {
      toast.error("Unesite broj telefona");
      return;
    }

    setIsAdding(true);
    try {
      await axios.post(`${API}/blacklist?phone=${encodeURIComponent(newPhone)}`, {}, { headers });
      toast.success("Broj dodat na crnu listu");
      setNewPhone("");
      fetchBlacklist();
    } catch (error) {
      toast.error("Greška pri dodavanju na crnu listu");
    } finally {
      setIsAdding(false);
    }
  };

  const handleRemoveFromBlacklist = async (phone) => {
    try {
      await axios.delete(`${API}/blacklist/${encodeURIComponent(phone)}`, { headers });
      toast.success("Broj uklonjen sa crne liste");
      fetchBlacklist();
    } catch (error) {
      toast.error("Greška pri uklanjanju sa crne liste");
    }
  };

  return (
    <div className="animate-fade-in">
      <h2 className="font-['Cormorant_Garamond'] text-3xl font-light mb-6">Crna Lista</h2>
      
      <p className="text-[#9CA3AF] mb-6">
        Blokirani brojevi telefona ne mogu praviti nove rezervacije u salonu.
      </p>

      {/* Add new phone */}
      <div className="bg-[var(--color-surface)] rounded-xl border border-[#2A2A2D] p-6 mb-6">
        <h3 className="font-medium mb-4">Dodaj broj na crnu listu</h3>
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Phone className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#9CA3AF]" />
            <Input
              value={newPhone}
              onChange={(e) => setNewPhone(e.target.value)}
              placeholder="+381 6X XXX XXXX"
              className="pl-12 bg-[var(--color-background)] border-[#2A2A2D] focus:border-[var(--color-primary)] w-full"
              data-testid="blacklist-phone-input"
              onKeyDown={(e) => e.key === "Enter" && handleAddToBlacklist()}
            />
          </div>
          <Button
            onClick={handleAddToBlacklist}
            disabled={isAdding}
            className="bg-red-500 hover:bg-red-600 text-white w-full sm:w-auto"
            data-testid="add-to-blacklist-btn"
          >
            <Ban className="w-4 h-4 mr-2" />
            Blokiraj
          </Button>
        </div>
      </div>

      {/* Blacklist table */}
      {loading ? (
        <div className="text-center py-12 text-[#9CA3AF]">Učitavanje...</div>
      ) : blacklist.length === 0 ? (
        <div className="text-center py-12 bg-[var(--color-surface)] rounded-xl border border-[#2A2A2D]">
          <Shield className="w-12 h-12 mx-auto text-[#9CA3AF] mb-4" />
          <p className="text-[#9CA3AF]">Nema blokiranih brojeva</p>
        </div>
      ) : (
        <div className="bg-[var(--color-surface)] rounded-xl border border-[#2A2A2D] overflow-hidden">
          {/* Desktop Table */}
          <div className="hidden sm:block">
            <Table>
              <TableHeader>
                <TableRow className="border-[#2A2A2D] hover:bg-transparent">
                  <TableHead className="text-[#9CA3AF]">Broj telefona</TableHead>
                  <TableHead className="text-[#9CA3AF]">Datum blokiranja</TableHead>
                  <TableHead className="text-[#9CA3AF] text-right">Akcija</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {blacklist.map((item, index) => (
                  <TableRow key={index} className="border-[#2A2A2D]" data-testid={`blacklist-row-${index}`}>
                    <TableCell className="font-medium">
                      <div className="flex items-center gap-2">
                        <Ban className="w-4 h-4 text-red-400" />
                        {item.phone}
                      </div>
                    </TableCell>
                    <TableCell className="text-[#9CA3AF]">
                      {item.created_at ? format(new Date(item.created_at), "d. MMM yyyy HH:mm", { locale: sr }) : "-"}
                    </TableCell>
                    <TableCell className="text-right">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleRemoveFromBlacklist(item.phone)}
                        className="border-green-400/30 text-green-400 hover:bg-green-400/10"
                        data-testid={`unblock-${index}`}
                      >
                        <Check className="w-4 h-4 mr-1" />
                        Odblokiraj
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>

          {/* Mobile Card Layout */}
          <div className="sm:hidden divide-y divide-[#2A2A2D]">
            {blacklist.map((item, index) => (
              <div key={index} className="p-4 flex items-center justify-between gap-3" data-testid={`blacklist-mobile-${index}`}>
                <div className="min-w-0">
                  <div className="flex items-center gap-2 font-medium">
                    <Ban className="w-4 h-4 text-red-400 shrink-0" />
                    <span className="truncate">{item.phone}</span>
                  </div>
                  <div className="text-xs text-[#9CA3AF] mt-1">
                    {item.created_at ? format(new Date(item.created_at), "d. MMM yyyy HH:mm", { locale: sr }) : "-"}
                  </div>
                </div>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleRemoveFromBlacklist(item.phone)}
                  className="border-green-400/30 text-green-400 hover:bg-green-400/10 shrink-0"
                >
                  <Check className="w-4 h-4 mr-1" />
                  Odblokiraj
                </Button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};



export default BlacklistPage;
