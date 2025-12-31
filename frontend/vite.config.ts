import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";

// https://vitejs.dev/config/
export default defineConfig(() => ({
  server: {
    host: "::",
    port: 8080,
  },
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          // React ecosystem
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],

          // TanStack Query
          'react-query': ['@tanstack/react-query'],

          // Markdown rendering (already loaded via ChatMessage)
          'markdown': [
            'react-markdown',
            'remark-gfm',
            'rehype-highlight',
            'rehype-raw'
          ],

          // Radix UI components (shadcn/ui)
          'radix-ui': [
            '@radix-ui/react-dialog',
            '@radix-ui/react-dropdown-menu',
            '@radix-ui/react-scroll-area',
            '@radix-ui/react-tabs',
            '@radix-ui/react-toast',
            '@radix-ui/react-progress',
            '@radix-ui/react-avatar',
            '@radix-ui/react-label',
            '@radix-ui/react-select',
            '@radix-ui/react-switch',
            '@radix-ui/react-checkbox',
            '@radix-ui/react-radio-group',
          ],

          // Icon library
          'lucide': ['lucide-react'],
        },
      },
    },
    chunkSizeWarningLimit: 600, // Slightly higher for vendor chunks
  },
}));
