import { useMemo } from "react";
import { useNavigate } from "react-router-dom";
import clsx from "clsx";
import { useCreationStore } from "@/store/creationStore";
import { useCareerStore } from "@/store/careerStore";
import { careerApi } from "@/api/careerApi";
import IdentityStep from "./steps/IdentityStep";
import OriginStep from "./steps/OriginStep";
import PositionStep from "./steps/PositionStep";
import LeagueStep from "./steps/LeagueStep";
import TeamStep from "./steps/TeamStep";
import ReviewStep from "./steps/ReviewStep";

const STEPS = [
  { id: "identity", label: "Identidad", component: IdentityStep },
  { id: "origin", label: "Origen", component: OriginStep },
  { id: "position", label: "Posición", component: PositionStep },
  { id: "league", label: "Liga", component: LeagueStep },
  { id: "team", label: "Equipo", component: TeamStep },
  { id: "review", label: "Confirmar", component: ReviewStep },
] as const;

export default function CreationLayout() {
  const step = useCreationStore((state) => state.step);
  const draft = useCreationStore((state) => state.draft);
  const setStep = useCreationStore((state) => state.setStep);
  const reset = useCreationStore((state) => state.reset);
  const setSession = useCareerStore((state) => state.setSession);
  const setLoading = useCareerStore((state) => state.setLoading);
  const setError = useCareerStore((state) => state.setError);
  const navigate = useNavigate();

  const StepComponent = STEPS[step].component;

  const canAdvance = useMemo(() => {
    switch (STEPS[step].id) {
      case "identity":
        return draft.firstName.trim() && draft.lastName.trim();
      case "origin":
        return Boolean(draft.birthCountry);
      case "position":
        return Boolean(draft.position);
      case "league":
        return Boolean(draft.startingLeague);
      case "team":
        return true;
      case "review":
        return true;
    }
  }, [step, draft]);

  const handleNext = async () => {
    if (step < STEPS.length - 1) {
      setStep(step + 1);
      return;
    }
    try {
      setLoading(true);
      setError(null);
      const session = await careerApi.create({ mode: "player", draft });
      setSession(session);
      reset();
      navigate("/career");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error inesperado");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <ol className="flex flex-wrap items-center gap-2 text-xs">
        {STEPS.map((s, index) => (
          <li key={s.id} className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => index < step && setStep(index)}
              disabled={index > step}
              className={clsx(
                "px-3 py-1 rounded uppercase tracking-widest border transition-colors",
                index === step
                  ? "border-barrio-accent text-barrio-accent"
                  : index < step
                    ? "border-barrio-border text-barrio-muted hover:text-barrio-text"
                    : "border-barrio-border/50 text-barrio-muted/50",
              )}
            >
              {index + 1}. {s.label}
            </button>
            {index < STEPS.length - 1 && (
              <span className="text-barrio-muted/40">›</span>
            )}
          </li>
        ))}
      </ol>

      <div className="panel p-6 min-h-[420px]">
        <StepComponent />
      </div>

      <div className="flex justify-between">
        <button
          type="button"
          className="btn"
          onClick={() => setStep(Math.max(0, step - 1))}
          disabled={step === 0}
        >
          Atrás
        </button>
        <button
          type="button"
          className="btn btn-primary"
          disabled={!canAdvance}
          onClick={handleNext}
        >
          {step === STEPS.length - 1 ? "Iniciar carrera" : "Siguiente"}
        </button>
      </div>
    </div>
  );
}
