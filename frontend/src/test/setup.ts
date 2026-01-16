import "@testing-library/jest-dom/vitest";

Element.prototype.scrollIntoView = () => undefined;
window.requestAnimationFrame = (callback: FrameRequestCallback) => {
  callback(0);
  return 1;
};
