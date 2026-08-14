import type { Position } from "@/types/game";

interface PositionInfo {
  code: Position;
  name: string;
  fullName: string;
  category: "goalkeeper" | "defender" | "midfielder" | "forward";
  primaryStats: string[];
}

export const POSITIONS: PositionInfo[] = [
  {
    code: "GK",
    name: "Arquero",
    fullName: "Goalkeeper",
    category: "goalkeeper",
    primaryStats: ["Reflejos", "Posicionamiento", "Manos"],
  },
  {
    code: "CB",
    name: "Central",
    fullName: "Center Back",
    category: "defender",
    primaryStats: ["Marca", "Cabezazo", "Fuerza"],
  },
  {
    code: "LB",
    name: "Lateral Izq.",
    fullName: "Left Back",
    category: "defender",
    primaryStats: ["Velocidad", "Resistencia", "Centros"],
  },
  {
    code: "RB",
    name: "Lateral Der.",
    fullName: "Right Back",
    category: "defender",
    primaryStats: ["Velocidad", "Resistencia", "Centros"],
  },
  {
    code: "CDM",
    name: "Volante Central",
    fullName: "Defensive Midfielder",
    category: "midfielder",
    primaryStats: ["Recuperación", "Pase", "Visión"],
  },
  {
    code: "CM",
    name: "Mediocampista",
    fullName: "Central Midfielder",
    category: "midfielder",
    primaryStats: ["Pase", "Visión", "Resistencia"],
  },
  {
    code: "CAM",
    name: "Enganche",
    fullName: "Attacking Midfielder",
    category: "midfielder",
    primaryStats: ["Visión", "Regate", "Tiro"],
  },
  {
    code: "LW",
    name: "Extremo Izq.",
    fullName: "Left Winger",
    category: "forward",
    primaryStats: ["Velocidad", "Regate", "Definición"],
  },
  {
    code: "RW",
    name: "Extremo Der.",
    fullName: "Right Winger",
    category: "forward",
    primaryStats: ["Velocidad", "Regate", "Definición"],
  },
  {
    code: "ST",
    name: "Delantero",
    fullName: "Striker",
    category: "forward",
    primaryStats: ["Definición", "Cabezazo", "Posicionamiento"],
  },
];
