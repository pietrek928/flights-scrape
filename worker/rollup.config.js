// rollup.config.js
import { resolve } from 'path';
import { nodeResolve } from '@rollup/plugin-node-resolve';
import commonjs from '@rollup/plugin-commonjs';
import livereload from 'rollup-plugin-livereload';
import copy from 'rollup-plugin-copy';

const watch = process.env.WATCH === 'true';
const inputJS = process.env.INPUT_JS;

export default {
    input: {
        [inputJS]: resolve(__dirname, 'code/' + inputJS + '.js'),
    },
    output: {
        dir: 'addon',
        format: 'iife',
        entryFileNames: `[name].js`,
        assetFileNames: `[name].[ext]`,
        manualChunks: (id) => null,
    },
    plugins: [
        nodeResolve(), // Finds modules in node_modules
        commonjs(),    // Converts CommonJS modules to ES6
        copy({
            targets: [
                { src: 'code/manifest.json', dest: 'addon' }
            ]
        }),
        watch && livereload({
            watch: 'addon',
        }),
    ],
};
