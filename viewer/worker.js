/**
 * OpenSCAD WASM compilation worker.
 *
 * Multi-file support: data.deps is a { filename: content } map of all other
 * .scad files in the same folder. They are written to the virtual FS root so
 * that include <file.scad> / use <file.scad> directives resolve correctly.
 *
 * Instance recycling: callMain() calls exit() after each run, terminating the
 * WASM runtime. We use a fresh instance per compilation and pre-warm the next
 * one in the background so the re-init cost is hidden behind editing time.
 */
import OpenSCAD   from '/wasm/openscad.js';
import { addFonts } from '/wasm/openscad.fonts.js';

async function createInstance() {
  const sc = await OpenSCAD({ noInitialRun: true });
  addFonts(sc);
  return sc;
}

let instanceReady = createInstance();

instanceReady
  .then(() => self.postMessage({ type: 'ready' }))
  .catch(e => self.postMessage({ type: 'init_error', message: String(e) }));

self.onmessage = async ({ data }) => {
  if (data.type !== 'compile') return;

  let sc;
  try {
    sc = await instanceReady;
  } catch (e) {
    self.postMessage({ type: 'error', message: 'OpenSCAD 初始化失败: ' + String(e) });
    return;
  }

  instanceReady = createInstance();

  try {
    // Write the main file
    try { sc.FS.unlink('/input.scad'); } catch {}
    sc.FS.writeFile('/input.scad', data.source);

    // Write all dependency files (include / use targets)
    for (const [name, content] of Object.entries(data.deps || {})) {
      try { sc.FS.unlink('/' + name); } catch {}
      sc.FS.writeFile('/' + name, content);
    }

    try { sc.FS.unlink('/output.stl'); } catch {}

    const args = ['/input.scad', '--enable=manifold', '-o', '/output.stl'];
    if (data.fn) args.push('-D', `$fn=${data.fn}`);

    const exitCode = sc.callMain(args);
    if (exitCode !== 0) {
      self.postMessage({ type: 'error', message: `编译退出码 ${exitCode}` });
      return;
    }

    const stl = sc.FS.readFile('/output.stl');
    self.postMessage({ type: 'result', stl: stl.buffer }, [stl.buffer]);
  } catch (e) {
    self.postMessage({ type: 'error', message: String(e) });
  }
};
