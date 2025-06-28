import { resolve } from 'path';
import { defineConfig } from 'vite';

export default defineConfig({
    build: {
        outDir: 'addon',
        rollupOptions: {
            input: {
                ryanair: resolve(__dirname, 'code/ryanair.js'),
                wizzair: resolve(__dirname, 'code/wizzair.js'),
            },
            output: {
                entryFileNames: `[name].js`,
                chunkFileNames: `[name].js`,
                assetFileNames: `[name].[ext]`
            }
        },
    },
});