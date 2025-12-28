import { useEffect, useRef, useState } from "react";
import { AlertCircle } from "lucide-react";

interface MermaidDiagramProps {
  chart: string;
}

export function MermaidDiagram({ chart }: MermaidDiagramProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [svg, setSvg] = useState<string>("");

  useEffect(() => {
    // Skip if no chart content
    if (!chart || !chart.trim()) {
      setError("Empty diagram content");
      setIsLoading(false);
      return;
    }

    let mounted = true;

    const renderDiagram = async () => {
      try {
        setIsLoading(true);
        setError(null);

        console.log("Starting mermaid diagram render for:", chart.substring(0, 50) + "...");

        // Dynamic import to reduce bundle size
        const mermaid = (await import("mermaid")).default;

        // Initialize mermaid with dark theme matching design system
        mermaid.initialize({
          startOnLoad: false,
          theme: "dark",
          themeVariables: {
            primaryColor: "#a78bfa", // --primary (purple) converted from HSL
            primaryTextColor: "#fff",
            primaryBorderColor: "#22d3ee", // --accent (cyan) converted from HSL
            lineColor: "#9ca3af",
            secondaryColor: "#22d3ee",
            tertiaryColor: "#2d3748",
            background: "#1a1f2e",
            mainBkg: "#1a1f2e",
            nodeBorder: "#a78bfa",
            clusterBkg: "#252d3d",
            clusterBorder: "#2d3748",
            defaultLinkColor: "#22d3ee",
            titleColor: "#f3f4f6",
            edgeLabelBackground: "#1a1f2e",
            nodeTextColor: "#fff",
            fontSize: "14px",
            fontFamily: "Space Grotesk, system-ui, sans-serif",
          },
          flowchart: {
            useMaxWidth: true,
            htmlLabels: true,
            curve: "basis",
          },
          sequence: {
            useMaxWidth: true,
          },
          gantt: {
            useMaxWidth: true,
          },
        });

        console.log("Mermaid initialized, rendering...");

        // Generate unique ID to support multiple diagrams
        const id = `mermaid-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

        // Render the diagram
        const result = await mermaid.render(id, chart.trim());

        console.log("Mermaid render complete, updating state");

        // Update state with the SVG
        if (mounted) {
          setSvg(result.svg);
          setIsLoading(false);
          console.log("Diagram rendered successfully");
        }
      } catch (err) {
        if (mounted) {
          const errorMessage =
            err instanceof Error ? err.message : "Unknown error occurred";
          console.error("Mermaid rendering error:", errorMessage, "\nChart:", chart);
          setError(errorMessage);
          setIsLoading(false);
        }
      }
    };

    renderDiagram();

    // Cleanup function
    return () => {
      mounted = false;
    };
  }, [chart]);

  // Error state - show error message with fallback code block
  if (error) {
    return (
      <div className="rounded-lg bg-destructive/10 border border-destructive/30 p-4 my-4">
        <div className="flex items-center gap-2 text-sm font-semibold text-destructive mb-2">
          <AlertCircle className="h-4 w-4" />
          <span>Mermaid Diagram Error</span>
        </div>
        <p className="text-xs text-destructive/80 mb-3">{error}</p>
        <details className="text-xs">
          <summary className="cursor-pointer text-muted-foreground hover:text-foreground mb-2">
            Show diagram code
          </summary>
          <pre className="overflow-x-auto rounded bg-slate-900 p-3 text-slate-300 font-mono text-xs">
            <code>{chart}</code>
          </pre>
        </details>
      </div>
    );
  }

  // Loading state
  if (isLoading) {
    return (
      <div className="rounded-lg bg-card p-4 my-4 border border-border/50">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <div className="h-4 w-4 animate-spin rounded-full border-2 border-muted-foreground border-t-transparent" />
          <span>Rendering diagram...</span>
        </div>
      </div>
    );
  }

  // Render the diagram
  return (
    <div
      ref={containerRef}
      className="rounded-lg bg-card p-4 my-4 border border-border/50 overflow-x-auto mermaid-diagram"
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  );
}
