/**
 * Multi-layer conic sweep (Gradient 7) — decorative frame.
 * Includes a neutral base behind the layers so black conics don’t disappear on dark page backgrounds.
 */
export function Gradient7() {
  return (
    <div className="relative group w-full aspect-video min-h-[12rem] overflow-hidden rounded-xl border border-dashed border-border">
      <div className="absolute inset-0 pointer-events-none border-b border-l border-dashed border-foreground/25 rounded-xl z-10" aria-hidden />
      <div className="w-full h-full min-h-[inherit] relative flex items-center justify-center overflow-hidden bg-background/50">
        {/* Without this, stacked black conics read as solid black on dark themes (invisible). */}
        <div className="absolute inset-0 bg-[#ececee] dark:bg-[#3a3a42]" aria-hidden />
        <div
          style={{
            background:
              "conic-gradient(from 135deg at 50% 50%, rgba(0, 0, 0, 0) 0deg, #000000 360deg), conic-gradient(from 44.87deg at 50% 50%, rgba(0, 0, 0, 0) 0deg, #000000 360deg), conic-gradient(from -89.88deg at 50% 50%, #FFFFFF 0deg, #999999 360deg)",
          }}
          className="absolute inset-0"
        />
      </div>
      <div className="leading-none absolute left-2 bottom-2 z-40">
        <p className="text-xs font-medium text-foreground drop-shadow-[0_1px_1px_rgba(255,255,255,0.8)] dark:drop-shadow-[0_1px_2px_rgba(0,0,0,0.9)]">
          Gradient 7
        </p>
        <p className="text-[8px] text-foreground/90 dark:text-foreground/80 dark:drop-shadow-[0_1px_2px_rgba(0,0,0,0.9)]">
          Multi-layer conic sweep
        </p>
      </div>
    </div>
  );
}

export default Gradient7;
