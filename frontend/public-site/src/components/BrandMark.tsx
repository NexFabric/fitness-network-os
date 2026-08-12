export function BrandMark({
  size = "md",
  showWordmark = true,
}: {
  size?: "sm" | "md";
  showWordmark?: boolean;
}) {
  const box = size === "sm" ? "h-8 w-8" : "h-9 w-9";
  const icon = size === "sm" ? 14 : 16;

  return (
    <span className="inline-flex items-center gap-2.5">
      <span
        className={`flex ${box} items-center justify-center rounded-lg bg-brand/15 border border-brand/25 text-brand shadow-sm`}
        aria-hidden="true"
      >
        <svg
          width={icon}
          height={icon}
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
        </svg>
      </span>
      {showWordmark && (
        <span className="text-lg font-bold tracking-tight text-foreground">
          GymClubNex
        </span>
      )}
    </span>
  );
}
