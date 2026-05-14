/**
 * OpenSCAD WASM compilation worker.
 *
 * Problem: Emscripten's callMain() calls exit() internally, which terminates
 * the WASM runtime after the first use. Reusing the same instance causes
 * garbage exit codes on the second call.
 *
 * Fix: create a fresh OpenSCAD instance for each compilation. To avoid the
 * re-init wait, we immediately pre-warm the NEXT instance in the background
 * as soon as a compilation begins. openscad.js caches the downloaded WASM JS
 * text, so subsequent instantiations only re-run WASM init from the
 * browser-cached binary — typically < 2s.
 */
import OpenSCAD from '/wasm/openscad.js';

// Always a Promise<instance> pointing to the next ready instance.
let instanceReady = OpenSCAD({ noInitialRun: true });

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

  // Pre-warm next instance in background while this compilation runs.
  instanceReady = OpenSCAD({ noInitialRun: true });

  try {
    try { sc.FS.unlink('/input.scad'); } catch {}
    try { sc.FS.unlink('/output.stl'); } catch {}

    sc.FS.writeFile('/input.scad', data.source);

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
