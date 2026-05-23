import { useRef, useState, useLayoutEffect } from "react";
import { gsap } from "gsap";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const GRID_8: [number, number] = [8, 8];

/**
 * GSAP grid stagger demo (pixel-perfect registry block).
 * Uses CSS grid (8×8) so stagger math matches layout; intro + ripple run without relying on nested stagger.onStart.
 */
const Stagger1 = () => {
  const rootRef = useRef<HTMLDivElement>(null);
  const [fromIndex, setFromIndex] = useState(27);
  const [animating, setAnimating] = useState(false);

  useLayoutEffect(() => {
    const root = rootRef.current;
    if (!root) return;

    const ctx = gsap.context(() => {
      const blocks = gsap.utils.toArray<HTMLElement>(
        root.querySelectorAll(".stagger-cell")
      );
      if (blocks.length === 0) return;

      gsap.set(blocks, { transformOrigin: "50% 50%" });
      gsap.from(blocks, {
        opacity: 0.35,
        scale: 0.45,
        duration: 0.45,
        stagger: { grid: GRID_8, from: "center", each: 0.02 },
        ease: "back.out(1.6)",
        delay: 0.2,
        clearProps: "opacity",
      });
    }, root);

    return () => ctx.revert();
  }, []);

  const handleRipple = () => {
    const root = rootRef.current;
    if (animating || !root) return;
    setAnimating(true);

    const blocks = gsap.utils.toArray<HTMLElement>(
      root.querySelectorAll(".stagger-cell")
    );
    if (blocks.length === 0) {
      setAnimating(false);
      return;
    }

    gsap.killTweensOf(blocks);
    gsap.set(blocks, { transformOrigin: "50% 50%" });

    gsap.to(blocks, {
      scale: 1.2,
      duration: 0.22,
      stagger: { grid: GRID_8, from: fromIndex, each: 0.038 },
      yoyo: true,
      repeat: 1,
      ease: "power2.out",
      onComplete: () => setAnimating(false),
    });
  };

  return (
    <div ref={rootRef} className="mx-auto w-full max-w-md">
      <p className="mb-3 text-center text-xs text-muted-foreground">
        Tap a square to choose the wave origin, then press{" "}
        <span className="font-medium text-foreground">Ripple</span>.
      </p>
      <div className="mx-auto w-fit rounded-xl bg-muted/30 p-3 ring-1 ring-border/80">
        <div
          className="grid w-[calc(8*2.5rem+7*0.5rem)] grid-cols-8 gap-2"
          style={{ gridTemplateRows: "repeat(8, minmax(0, 1fr))" }}
        >
          {Array.from({ length: 64 }).map((_, index) => (
            <div
              key={index}
              className={cn(
                "stagger-cell h-10 w-10 cursor-pointer rounded-md border border-border/70 shadow-sm will-change-transform",
                index === fromIndex
                  ? "bg-[hsl(var(--satya-saffron))]/50 ring-2 ring-[hsl(var(--satya-saffron))]/40"
                  : "bg-muted"
              )}
              onClick={() => setFromIndex(index)}
              title={`Ripple origin: cell ${index}`}
              role="presentation"
            />
          ))}
        </div>
      </div>
      <div className="flex justify-center">
        <Button
          type="button"
          variant="outline"
          size="sm"
          className="mt-6 text-xs transition-all duration-200 active:scale-[0.94]"
          onClick={handleRipple}
          disabled={animating}
        >
          Ripple
        </Button>
      </div>
    </div>
  );
};

export default Stagger1;
