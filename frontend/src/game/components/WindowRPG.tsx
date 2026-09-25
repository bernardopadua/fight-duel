import { motion } from "framer-motion";

export function WindowRPG(
    { 
        children,
        title,
        icon,
        rightSide,
        parentContainerRef,
        onClose
    }: 
    { 
        children: React.ReactNode,
        title: string,
        icon: string,
        rightSide: React.ReactNode,
        parentContainerRef: React.RefObject<HTMLDivElement>,
        onClose?: () => void
     }
){
    return (
        <motion.div drag dragMomentum={false} dragElastic={0}
            dragConstraints={parentContainerRef}
            onPointerDown={(e)=>{ e.stopPropagation(); }}
            onMouseDown={(e)=>{ e.stopPropagation(); }}
            className="relative w-60 rounded border-2 border-amber-700/80 
                scale-65 sm:scale-90 md:scale-100
                bg-gradient-to-b from-stone-900/95 via-neutral-950/95 to-black/95 
                p-4 text-stone-200 backdrop-blur-md ring-1 ring-amber-500/30"
            >

            <span className="absolute -top-1 -left-1 h-2.5 w-2.5 rotate-45 border border-amber-300 bg-amber-600 shadow-[0_0_6px_#f59e0b]" />
            <span className="absolute -top-1 -right-1 h-2.5 w-2.5 rotate-45 border border-amber-300 bg-amber-600 shadow-[0_0_6px_#f59e0b]" />
            <span className="absolute -bottom-1 -left-1 h-2.5 w-2.5 rotate-45 border border-amber-300 bg-amber-600 shadow-[0_0_6px_#f59e0b]" />
            <span className="absolute -bottom-1 -right-1 h-2.5 w-2.5 rotate-45 border border-amber-300 bg-amber-600 shadow-[0_0_6px_#f59e0b]" />

            <div className="flex items-center justify-between border-b border-amber-700/50 pb-2 mb-3">
                <div className="flex items-center gap-2">
                    <span className="text-base">{icon}</span>
                    <h2 className="font-['Cinzel'] text-xs font-bold tracking-widest text-amber-400 uppercase drop-shadow">
                        {title}
                    </h2>
                </div>
                <div className="flex items-center gap-2">
                    {rightSide}
                    {onClose && (
                        <button
                            type="button"
                            onClick={onClose}
                            className="text-stone-400 hover:text-amber-300 hover:scale-110 active:scale-95 text-xs font-bold transition-all cursor-pointer leading-none px-1"
                        >
                            ✕
                        </button>
                    )}
                </div>
            </div>
            {children}
        </motion.div>
    );
}