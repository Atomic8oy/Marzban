import {
    useSortable,
} from "@dnd-kit/sortable"
import { CSS } from "@dnd-kit/utilities"
import { UniqueIdentifier } from "@dnd-kit/core"

import { BaseHost, removeHost, modifyHost } from "@/service/api"
import { Card } from "../ui/card"
import { Copy, GripVertical, MoreVertical, Pencil, Power, Trash2 } from "lucide-react"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from "../ui/dropdown-menu"
import { Button } from "../ui/button"
import { useTranslation } from "react-i18next"
import useDirDetection from "@/hooks/use-dir-detection"
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from "../ui/alert-dialog"
import { cn } from "@/lib/utils"
import { toast } from "@/hooks/use-toast"
import { useState } from "react"
import { queryClient } from "@/utils/query-client"

interface SortableHostProps {
    host: BaseHost;
    onEdit: (host: BaseHost) => void;
    onDuplicate: (host: BaseHost) => Promise<void>;
}

const DeleteAlertDialog = ({
    host,
    isOpen,
    onClose,
    onConfirm,
}: {
    host: BaseHost;
    isOpen: boolean;
    onClose: () => void;
    onConfirm: () => void;
}) => {
    const { t } = useTranslation();
    const dir = useDirDetection();

    return (
        <AlertDialog open={isOpen} onOpenChange={onClose}>
            <AlertDialogContent>
                <AlertDialogHeader className={cn(dir === "rtl" && "sm:text-right")}>
                    <AlertDialogTitle>{t("deleteHost.title")}</AlertDialogTitle>
                    <AlertDialogDescription>
                        <span dir={dir} dangerouslySetInnerHTML={{ __html: t("deleteHost.prompt", { name: host.remark ?? "" }) }} />
                    </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter className={cn(dir === "rtl" && "sm:gap-x-2 sm:flex-row-reverse")}>
                    <AlertDialogCancel onClick={onClose}>{t("cancel")}</AlertDialogCancel>
                    <AlertDialogAction variant="destructive" onClick={onConfirm}>
                        {t("delete")}
                    </AlertDialogAction>
                </AlertDialogFooter>
            </AlertDialogContent>
        </AlertDialog>
    );
};

export default function SortableHost({ host, onEdit, onDuplicate }: SortableHostProps) {
    const [isDeleteDialogOpen, setDeleteDialogOpen] = useState(false);
    const { t } = useTranslation();
    
    // Ensure host.id is not null before using it
    if (!host.id) {
        return null;
    }

    const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ 
        id: host.id as UniqueIdentifier 
    })

    const style = {
        transform: CSS.Transform.toString(transform),
        transition,
        zIndex: isDragging ? 2 : 1,
        opacity: isDragging ? 0.8 : 1,
    }
    const cursor = isDragging ? "grabbing" : "grab";

    const handleToggleStatus = async () => {
        if (!host.id) return;
        
        try {
            // Create updated host data with toggled is_disabled status
            const updatedHost = {
                ...host,
                is_disabled: !host.is_disabled
            };
            
            await modifyHost(host.id, updatedHost);
            
            toast({
                title: t('success', { defaultValue: 'Success' }),
                description: t(host.is_disabled ? "host.enableSuccess" : "host.disableSuccess", { 
                    name: host.remark ?? "",
                    defaultValue: `Host "{name}" has been ${host.is_disabled ? 'enabled' : 'disabled'} successfully`
                })
            });
            
            // Invalidate the hosts query to refresh the list
            queryClient.invalidateQueries({
                queryKey: ["getGetHostsQueryKey"],
            });
        } catch (error) {
            toast({
                title: t('error', { defaultValue: 'Error' }),
                description: t(host.is_disabled ? "host.enableFailed" : "host.disableFailed", { 
                    name: host.remark ?? "",
                    defaultValue: `Failed to ${host.is_disabled ? 'enable' : 'disable'} host "{name}"`
                }),
                variant: "destructive"
            });
        }
    };

    const handleDeleteClick = (event: Event) => {
        event.stopPropagation();
        setDeleteDialogOpen(true);
    };

    const handleConfirmDelete = async () => {
        if (!host.id) return;
        
        try {
            await removeHost(host.id)
            toast({
                title: t('success', { defaultValue: 'Success' }),
                description: t("deleteHost.deleteSuccess", { 
                    name: host.remark ?? "",
                    defaultValue: 'Host "{name}" has been deleted successfully'
                })
            })
            setDeleteDialogOpen(false);
            queryClient.invalidateQueries({
                queryKey: ["getGetHostsQueryKey"],
            });
        }
        catch (error) {
            toast({
                title: t('error', { defaultValue: 'Error' }),
                description: t("deleteHost.deleteFailed", { 
                    name: host.remark ?? "",
                    defaultValue: 'Failed to delete host "{name}"'
                }),
                variant: "destructive"
            })
        }
    };

    return (
        <div ref={setNodeRef} className="cursor-default" style={style} {...attributes}>
            <Card className="p-4 relative group h-full hover:bg-accent transition-colors">
                <div className="flex items-center gap-3">
                    <button style={{ cursor: cursor }} className="touch-none opacity-50 group-hover:opacity-100 transition-opacity" {...listeners}>
                        <GripVertical className="h-5 w-5" />
                        <span className="sr-only">Drag to reorder</span>
                    </button>
                    <div 
                        className="flex-1 min-w-0 cursor-pointer" 
                        onClick={() => onEdit(host)}
                    >
                        <div className="flex items-center gap-2">
                            <div className={cn(
                                "min-h-2 min-w-2 rounded-full",
                                host.is_disabled ? "bg-red-500" : "bg-green-500"
                            )} />
                            <div className="font-medium truncate">{host.remark ?? ""}</div>
                        </div>
                        <div className="text-sm text-muted-foreground truncate">{host.address ?? ""}</div>
                    </div>
                    <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon">
                                <MoreVertical className="h-4 w-4" />
                            </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                            <DropdownMenuItem onSelect={(e) => {
                                e.stopPropagation()
                                handleToggleStatus()
                            }}>
                                <Power className="h-4 w-4 mr-2" />
                                {host?.is_disabled ? t("enable") : t("disable")}
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem onSelect={(e) => {
                                e.stopPropagation()
                                onEdit(host)
                            }}>
                                <Pencil className="h-4 w-4 mr-2" />
                                {t("edit")}
                            </DropdownMenuItem>
                            <DropdownMenuItem onSelect={(e) => {
                                e.stopPropagation()
                                onDuplicate(host)
                            }}>
                                <Copy className="h-4 w-4 mr-2" />
                                {t("duplicate")}
                            </DropdownMenuItem>
                            <DropdownMenuItem 
                                onSelect={handleDeleteClick}
                                className="text-destructive"
                            >
                                <Trash2 className="h-4 w-4 mr-2" />
                                {t("delete")}
                            </DropdownMenuItem>
                        </DropdownMenuContent>
                    </DropdownMenu>
                </div>
            </Card>

            <DeleteAlertDialog
                host={host}
                isOpen={isDeleteDialogOpen}
                onClose={() => setDeleteDialogOpen(false)}
                onConfirm={handleConfirmDelete}
            />
        </div>
    )
}