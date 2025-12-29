import { memo } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import rehypeRaw from "rehype-raw";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Bot, User } from "lucide-react";
import { MermaidDiagram } from "@/components/MermaidDiagram";

interface ChatMessageProps {
  role: "user" | "assistant";
  content: string;
  timestamp?: string;
}

const ChatMessageComponent = ({ role, content, timestamp }: ChatMessageProps) => {
  const isUser = role === "user";

  return (
    <div className={`flex gap-3 ${isUser ? "flex-row-reverse" : "flex-row"}`}>
      {/* Avatar */}
      <Avatar className={`h-8 w-8 flex-shrink-0 ${isUser ? "bg-primary" : "bg-accent"}`}>
        <AvatarFallback className={isUser ? "bg-primary text-primary-foreground" : "bg-accent text-accent-foreground"}>
          {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
        </AvatarFallback>
      </Avatar>

      {/* Message Content */}
      <div className={`flex flex-col ${isUser ? "items-end" : "items-start"} max-w-[75%]`}>
        <div
          className={`rounded-2xl px-4 py-2.5 ${
            isUser
              ? "bg-primary text-primary-foreground rounded-tr-sm"
              : "bg-muted text-foreground rounded-tl-sm border border-border/50"
          }`}
        >
          {isUser ? (
            // User messages: plain text with preserved whitespace
            <p className="whitespace-pre-wrap break-words text-sm">{content}</p>
          ) : (
            // Assistant messages: rendered markdown with code highlighting
            <div className="prose prose-sm dark:prose-invert max-w-none">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                rehypePlugins={[rehypeHighlight, rehypeRaw]}
                components={{
                  // Customize code blocks
                  code: ({ node, className, children, ...props }) => {
                    const match = /language-(\w+)/.exec(className || "");
                    const isInline = !match;
                    const language = match?.[1];

                    if (isInline) {
                      return (
                        <code className="px-1.5 py-0.5 rounded bg-muted-foreground/10 text-foreground font-mono text-xs" {...props}>
                          {children}
                        </code>
                      );
                    }

                    // Render mermaid diagrams
                    if (language === "mermaid") {
                      return (
                        <MermaidDiagram
                          chart={String(children).replace(/\n$/, "")}
                        />
                      );
                    }

                    return (
                      <code className={className} {...props}>
                        {children}
                      </code>
                    );
                  },
                  pre: ({ children, ...props }) => (
                    <pre className="overflow-x-auto rounded-lg bg-slate-900 p-4 my-2" {...props}>
                      {children}
                    </pre>
                  ),
                  // Ensure links open in new tabs
                  a: ({ children, href, ...props }) => (
                    <a
                      href={href}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary hover:underline"
                      {...props}
                    >
                      {children}
                    </a>
                  ),
                  // Style lists
                  ul: ({ children, ...props }) => (
                    <ul className="list-disc list-inside space-y-1 my-2" {...props}>
                      {children}
                    </ul>
                  ),
                  ol: ({ children, ...props }) => (
                    <ol className="list-decimal list-inside space-y-1 my-2" {...props}>
                      {children}
                    </ol>
                  ),
                  // Style paragraphs
                  p: ({ children, ...props }) => (
                    <p className="mb-2 last:mb-0 leading-relaxed" {...props}>
                      {children}
                    </p>
                  ),
                }}
              >
                {content}
              </ReactMarkdown>
            </div>
          )}
        </div>

        {/* Timestamp */}
        {timestamp && (
          <span className="text-xs text-muted-foreground mt-1 px-1">
            {new Date(timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
          </span>
        )}
      </div>
    </div>
  );
};

// Memoize to prevent unnecessary re-renders when typing in input
export const ChatMessage = memo(ChatMessageComponent);
