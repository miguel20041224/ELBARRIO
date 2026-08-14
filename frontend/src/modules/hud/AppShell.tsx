import { NavLink } from "react-router-dom";
import type { PropsWithChildren } from "react";
import { useCareerStore } from "@/store/careerStore";
import clsx from "clsx";

export default function AppShell({ children }: PropsWithChildren) {
  const session = useCareerStore((state) => state.session);

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-barrio-border bg-barrio-panel/80 backdrop-blur-md">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <NavLink to="/" className="flex items-baseline gap-2">
            <span className="heading text-3xl text-barrio-accent">
              EL<span className="text-barrio-gold">BARRIO</span>
            </span>
            <span className="text-xs uppercase tracking-widest text-barrio-muted">
              Football Career
            </span>
          </NavLink>

          <nav className="flex items-center gap-4 text-sm">
            <NavItem to="/">Inicio</NavItem>
            <NavItem to="/create">Crear</NavItem>
            {session && <NavItem to="/career">Carrera</NavItem>}
          </nav>
        </div>
      </header>

      <main className="mx-auto w-full max-w-6xl flex-1 px-6 py-8">
        {children}
      </main>

      <footer className="border-t border-barrio-border py-4 text-center text-xs text-barrio-muted">
        ELBARRIO — Simulador de carrera futbolística
      </footer>
    </div>
  );
}

function NavItem({ to, children }: { to: string; children: string }) {
  return (
    <NavLink
      to={to}
      end
      className={({ isActive }) =>
        clsx(
          "uppercase tracking-widest transition-colors",
          isActive
            ? "text-barrio-accent"
            : "text-barrio-muted hover:text-barrio-text",
        )
      }
    >
      {children}
    </NavLink>
  );
}
