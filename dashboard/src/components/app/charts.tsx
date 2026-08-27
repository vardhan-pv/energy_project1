import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip as RTooltip,
  XAxis,
  YAxis,
} from "recharts";
import { fmtTime } from "@/lib/energy/format";

const axisStyle = { fontSize: 11, fill: "var(--color-muted-foreground)" };

const tooltipProps = {
  contentStyle: {
    background: "var(--color-popover)",
    border: "1px solid var(--color-border)",
    borderRadius: "10px",
    fontSize: "12px",
    color: "var(--color-popover-foreground)",
  },
  labelStyle: { color: "var(--color-muted-foreground)" },
};

export function PowerAreaChart({
  data,
  height = 260,
  color = "var(--color-chart-1)",
}: {
  data: { t: number; powerW: number }[];
  height?: number;
  color?: string;
}) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
        <defs>
          <linearGradient id="pw" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity={0.28} />
            <stop offset="100%" stopColor={color} stopOpacity={0.02} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
        <XAxis dataKey="t" tickFormatter={fmtTime} tick={axisStyle} tickLine={false} axisLine={false} minTickGap={40} />
        <YAxis tick={axisStyle} tickLine={false} axisLine={false} width={48} unit=" W" />
        <RTooltip
          {...tooltipProps}
          labelFormatter={(v) => fmtTime(Number(v))}
          formatter={(v: number | string) => [`${Number(v).toFixed(1)} W`, "Power"]}
        />
        <Area
          type="monotone"
          dataKey="powerW"
          stroke={color}
          strokeWidth={2}
          fill="url(#pw)"
          isAnimationActive={false}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}

export function MultiLineChart({
  data,
  series,
  height = 280,
  unit = " W",
}: {
  data: Record<string, number>[];
  series: { key: string; label: string; color: string }[];
  height?: number;
  unit?: string;
}) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
        <XAxis dataKey="t" tickFormatter={(v) => fmtTime(Number(v))} tick={axisStyle} tickLine={false} axisLine={false} minTickGap={40} />
        <YAxis tick={axisStyle} tickLine={false} axisLine={false} width={48} unit={unit} />
        <RTooltip {...tooltipProps} labelFormatter={(v) => fmtTime(Number(v))} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        {series.map((s) => (
          <Line
            key={s.key}
            type="monotone"
            dataKey={s.key}
            name={s.label}
            stroke={s.color}
            strokeWidth={2}
            dot={false}
            isAnimationActive={false}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}

export function ForecastChart({
  data,
  height = 220,
}: {
  data: { t: number; predictedW: number; lowerW: number; upperW: number }[];
  height?: number;
}) {
  const shaped = data.map((d) => ({ ...d, band: [d.lowerW, d.upperW] as [number, number] }));
  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={shaped} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
        <XAxis dataKey="t" tickFormatter={(v) => fmtTime(Number(v))} tick={axisStyle} tickLine={false} axisLine={false} minTickGap={40} />
        <YAxis tick={axisStyle} tickLine={false} axisLine={false} width={48} unit=" W" />
        <RTooltip
          {...tooltipProps}
          labelFormatter={(v) => fmtTime(Number(v))}
          formatter={(v: unknown, name: string) =>
            Array.isArray(v)
              ? [`${v[0].toFixed(0)} – ${v[1].toFixed(0)} W`, "Likely range"]
              : [`${Number(v).toFixed(1)} W`, name === "predictedW" ? "Forecast" : name]
          }
        />
        <Area
          type="monotone"
          dataKey="band"
          stroke="none"
          fill="var(--color-chart-4)"
          fillOpacity={0.14}
          isAnimationActive={false}
        />
        <Area
          type="monotone"
          dataKey="predictedW"
          stroke="var(--color-chart-4)"
          strokeWidth={2}
          strokeDasharray="5 4"
          fill="none"
          isAnimationActive={false}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}

export function DailyBarChart({
  data,
  height = 300,
}: {
  data: { date: string; laptop: number; kitchen_lights: number; office_fan: number; fridge: number }[];
  height?: number;
}) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
        <XAxis
          dataKey="date"
          tickFormatter={(v: string) => v.slice(5)}
          tick={axisStyle}
          tickLine={false}
          axisLine={false}
          minTickGap={16}
        />
        <YAxis tick={axisStyle} tickLine={false} axisLine={false} width={48} unit=" kWh" />
        <RTooltip {...tooltipProps} formatter={(v: number | string) => `${Number(v).toFixed(2)} kWh`} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Bar dataKey="fridge" name="Fridge" stackId="a" fill="var(--color-chart-1)" />
        <Bar dataKey="laptop" name="Laptop" stackId="a" fill="var(--color-chart-2)" />
        <Bar dataKey="office_fan" name="Office Fan" stackId="a" fill="var(--color-chart-3)" />
        <Bar dataKey="kitchen_lights" name="Kitchen Lights" stackId="a" fill="var(--color-chart-4)" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
