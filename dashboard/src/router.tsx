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

  // Polyfill router.stores: @tanstack/start-client-core's hydrateStart calls router.stores.ids.get().length.
  // Newer/mismatched router-core instances may not expose stores.ids immediately on client startup.
  let _stores = (router as any).stores;
  Object.defineProperty(router, "stores", {
    get() {
      if (!_stores) {
        _stores = {
          ids: {
            get: () => (router as any).state?.matches?.map((m: any) => m.routeId) || [],
          },
          matches: {
            get: () => (router as any).state?.matches || [],
          },
        };
      } else if (!_stores.ids) {
        _stores.ids = {
          get: () => _stores.matches?.get?.()?.map((m: any) => m.routeId) || (router as any).state?.matches?.map((m: any) => m.routeId) || [],
        };
      }
      return _stores;
    },
    set(v) {
      if (v && !v.ids) {
        v.ids = {
          get: () => v.matches?.get?.()?.map((m: any) => m.routeId) || (router as any).state?.matches?.map((m: any) => m.routeId) || [],
        };
      }
      _stores = v;
    },
    configurable: true,
    enumerable: true,
  });

  return router;
};
