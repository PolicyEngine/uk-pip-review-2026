"use client";

import { useEffect, useState } from "react";

// Window width, for layouts that change under 640px (as AB2026's useWidth).
export default function useWidth(fallback = 1200) {
  const [width, setWidth] = useState(fallback);
  useEffect(() => {
    const update = () => setWidth(window.innerWidth);
    update();
    window.addEventListener("resize", update);
    return () => window.removeEventListener("resize", update);
  }, []);
  return width;
}
