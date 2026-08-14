import clsx from "clsx";
import { COUNTRIES } from "@/data/countries";
import { useCreationStore } from "@/store/creationStore";

export default function OriginStep() {
  const country = useCreationStore((state) => state.draft.birthCountry);
  const update = useCreationStore((state) => state.update);

  return (
    <div className="space-y-6">
      <header>
        <h2 className="heading text-2xl">País de nacimiento</h2>
        <p className="text-sm text-barrio-muted">
          Tu país define tu selección nacional y cambia el prestigio inicial
          con el que la prensa te mira.
        </p>
      </header>

      <div className="grid gap-2 sm:grid-cols-3 md:grid-cols-4">
        {COUNTRIES.map((c) => {
          const selected = country === c.code;
          return (
            <button
              key={c.code}
              type="button"
              onClick={() => update({ birthCountry: c.code })}
              className={clsx(
                "flex items-center gap-3 rounded border px-3 py-2 text-left transition-colors",
                selected
                  ? "border-barrio-accent bg-barrio-accent/10"
                  : "border-barrio-border hover:border-barrio-muted",
              )}
            >
              <span className="text-2xl">{c.flag}</span>
              <div className="flex-1">
                <p className="text-sm font-semibold">{c.name}</p>
                <p className="text-xs text-barrio-muted">
                  Reputación: {c.reputation}
                </p>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
