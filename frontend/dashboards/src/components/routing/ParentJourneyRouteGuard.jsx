import { useEffect, useState } from "react";
import { Navigate, useLocation } from "react-router";
import {
  canAccessParentJourneyStage,
  loadParentJourneyOverview,
} from "../../features/parentJourney/parentJourneyState.js";

const SAFE_FALLBACK_PATH = "/parent";

export default function ParentJourneyRouteGuard({ stage, children }) {
  const location = useLocation();
  const [guardState, setGuardState] = useState({
    status: "loading",
    overview: null,
    errorMessage: "",
    stage,
  });

  useEffect(() => {
    let active = true;

    loadParentJourneyOverview()
      .then((overview) => {
        if (!active) return;

        setGuardState({
          status: "ready",
          overview,
          errorMessage: "",
          stage,
        });
      })
      .catch((error) => {
        if (!active) return;

        setGuardState({
          status: "error",
          overview: null,
          errorMessage: error instanceof Error ? error.message : String(error),
          stage,
        });
      });

    return () => {
      active = false;
    };
  }, [stage]);

  if (guardState.status === "loading" || guardState.stage !== stage) {
    return (
      <section aria-busy="true" style={{ padding: "24px 20px" }}>
        Checking parent journey state…
      </section>
    );
  }

  if (guardState.status === "error" || !canAccessParentJourneyStage(stage, guardState.overview)) {
    return (
      <Navigate
        to={SAFE_FALLBACK_PATH}
        replace
        state={{
          blockedParentJourneyStage: stage || null,
          parentJourneyError: guardState.errorMessage || null,
          from: location.pathname,
        }}
      />
    );
  }

  return children;
}
