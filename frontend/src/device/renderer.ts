const SOFTWARE_RENDERERS = [/swiftshader/i, /llvmpipe/i, /softpipe/i, /basic render driver/i, /software/i];

export function isSoftwareRenderer(name: string): boolean {
  return SOFTWARE_RENDERERS.some((pattern) => pattern.test(name));
}

function rendererOf(gl: WebGLRenderingContext): string {
  const info = gl.getExtension("WEBGL_debug_renderer_info");
  return String(gl.getParameter(info ? info.UNMASKED_RENDERER_WEBGL : gl.RENDERER));
}

export function softwareRendering(): boolean {
  try {
    const gl = document.createElement("canvas").getContext("webgl", { failIfMajorPerformanceCaveat: true });
    if (!gl) {
      return true;
    }
    const name = rendererOf(gl);
    gl.getExtension("WEBGL_lose_context")?.loseContext();
    return isSoftwareRenderer(name);
  } catch {
    return true;
  }
}

export function prefersLessTransparency(): boolean {
  return typeof matchMedia === "function" && matchMedia("(prefers-reduced-transparency: reduce)").matches;
}
