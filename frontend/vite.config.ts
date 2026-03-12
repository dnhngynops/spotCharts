import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// base: './' makes all asset paths relative so the build works
// correctly when deployed to a GitHub Pages subdirectory path.
export default defineConfig({
  plugins: [react()],
  base: './',
})
