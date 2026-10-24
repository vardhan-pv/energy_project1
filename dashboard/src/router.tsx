import { QueryClient } from "@tanstack/react-query";
import { createRouter } from "@tanstack/react-router";
import { routeTree } from "./routeTree.gen";

export const getRouter = () => {
  const queryClient = new QueryClient();

  const router = createRouter({
    routeTree,
    context: { queryClient },
    scrollRestoration: true,
    defaultPreloadStaleTime: 0,
  });

  // Polyfill getMatchedRoutes: newer @tanstack/react-router returns an object { matchedRoutes, routeParams, foundRoute }
  // while @tanstack/start-server-core expects an iterable array [matchedRoutes, rawParams, foundRoute].
  // By returning an array that also contains the object properties, both consumers work seamlessly.
  const origGetMatchedRoutes = router.getMatchedRoutes.bind(router);
  router.getMatchedRoutes = ((pathname: string) => {
    const res = origGetMatchedRoutes(pathname) as any;
    if (res && !Array.isArray(res)) {
      const arr: any = [res.matchedRoutes, res.routeParams, res.foundRoute];
      Object.assign(arr, res);
      return arr;
    }
    return res;
  }) as any;

  // Polyfill serverSsr methods: bridge differences between @tanstack/router-core and @tanstack/react-router SSR streaming
  let _serverSsr: any = undefined;
  Object.defineProperty(router, "serverSsr", {
    get() {
      return _serverSsr;
    },
    set(val) {
      if (val && typeof val === "object") {
        if (!val.takeBufferedScripts) {
          val.takeBufferedScripts = () => val.takeInitialHydrationScriptTags?.() || undefined;
        }
        if (!val.reserveStreamFastPath) {
          val.reserveStreamFastPath = () => true;
        }
        if (!val.onInjectedHtml) {
          val.onInjectedHtml = () => () => {};
        }
      }
      _serverSsr = val;
    },
    configurable: true,
    enumerable: true,
  });

  return router;
};
