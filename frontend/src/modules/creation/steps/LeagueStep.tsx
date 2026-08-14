import clsx from "clsx";
import { LEAGUES } from "@/data/leagues";
import { COUNTRIES } from "@/data/countries";
import { useCreationStore } from "@/store/creationStore";

function countryFlag(code: string) {
  return COUNTRIES.find((c) => c.code === code)?.flag ?? "🏳️";
}

function tierLabel(tier: number) {
  return "★".repeat(tier) + "☆".repeat(5 - tier);
}

export default function LeagueStep() {
  const league = useCreationStore((state) => state.draft.startingLeague);
  const update = useCreationStore((state) => state.update);

  return (
    <div className="space-y-6">
      <header>
        <h2 className="heading text-2xl">Liga inicial</h2>
        <p className="text-sm text-barrio-muted">
          Podés empezar en una liga fuerte con presión alta, o construir
          tu carrera desde abajo. Las ligas top pagan más pero castigan
          errores.
        </p>
      </header>

      <div className="grid gap-2 md:grid-cols-2">
        {LEAGUES.map((l) => {
          const selected = league === l.id;
          return (
            <button
              key={l.id}
              type="button"
              onClick={() => update({ startingLeague: l.id })}
              className={clsx(
                "rounded border p-4 text-left transition-colors",
                selected
                  ? "border-barrio-accent bg-barrio-accent/10"
                  : "border-barrio-border hover:border-barrio-muted",
              )}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-xl">{countryFlag(l.country)}</span>
                  <p className="font-semibold">{l.name}</p>
                </div>
                <span className="text-barrio-gold text-sm">
                  {tierLabel(l.tier)}
                </span>
              </div>
              <div className="mt-2 flex items-center justify-between text-xs text-barrio-muted">
                <span>Reputación: {l.reputation}</span>
                <span>Salario promedio: €{l.averageSalary.toLocaleString()}/sem</span>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
