"""
Performance comparison — Bokeh version of the original Dash app.

Everything (CSV parsing, "Name" transform, grouped-bar redraw) runs in
CustomJS in the browser, so the file produced by this script is a fully
standalone HTML page: no Bokeh server, no Python, no network access needed
to use it after it's generated.
"""

from bokeh.layouts import column, row
from bokeh.models import (
    ColumnDataSource,
    CustomJS,
    Div,
    FactorRange,
    FileInput,
    HoverTool,
)
from bokeh.plotting import figure
from bokeh.io import save, output_file
from bokeh.resources import INLINE

COLOR_RUN1 = "#1f77b4"  # blue  - matches Plotly's default qualitative palette
COLOR_RUN2 = "#ff7f0e"  # orange

# ---------------------------------------------------------------------------
# Data sources
# ---------------------------------------------------------------------------

# One hidden store per uploaded run. Mirrors the pandas df with a "Run"
# column added (here called "run") that holds the uploaded filename.
run1_store = ColumnDataSource(data=dict(name=[], median=[], run=[]))
run2_store = ColumnDataSource(data=dict(name=[], median=[], run=[]))

# Source actually driving the chart. "x" holds nested categorical factors
# of the form [name, run_label] so Bokeh groups bars by Name and colors
# them by Run, matching `px.bar(..., x="Name", color="Run", barmode="group")`.
plot_source = ColumnDataSource(data=dict(x=[], y=[], run=[], name=[], color=[]))

x_range = FactorRange(factors=[])

# ---------------------------------------------------------------------------
# Figure
# ---------------------------------------------------------------------------

p = figure(
    x_range=x_range,
    height=520,
    sizing_mode="stretch_width",
    title="Median Response Time by request",
    toolbar_location="above",
    tools="pan,wheel_zoom,box_zoom,reset,save",
)
p.vbar(
    x="x",
    top="y",
    width=0.8,
    source=plot_source,
    fill_color="color",
    line_color="color",
    legend_field="run",
)
p.add_tools(
    HoverTool(
        tooltips=[("Name", "@name"), ("Run", "@run"), ("Median Response Time", "@y")]
    )
)
# The x factors are [Name, run_label] pairs. Bokeh draws the leaf level
# (run_label) as the "major" tick labels right at the axis, and the outer
# level (Name) as the "group" labels with a separator line. We only want
# the Name to show -- the run is already conveyed by bar color + legend.
p.xaxis.major_label_text_font_size = "0pt"
p.xaxis.major_tick_line_color = None
p.xaxis.group_label_orientation = 0.785  # ~45 degrees, easier to read than 1.0 rad
p.yaxis.axis_label = "Median Response Time"
p.y_range.start = 0
p.legend.location = "top_right"
p.legend.title = "Run"

# ---------------------------------------------------------------------------
# JS helpers shared (duplicated, on purpose, in both callbacks below) -------
# ---------------------------------------------------------------------------

PARSE_CSV_JS = """
    function decodeBase64Utf8(b64) {
        const binary = atob(b64);
        const bytes = new Uint8Array(binary.length);
        for (let i = 0; i < binary.length; i++) {
            bytes[i] = binary.charCodeAt(i);
        }
        return new TextDecoder('utf-8').decode(bytes);
    }

    function parseCSV(text) {
        const rows = [];
        let row = [];
        let field = '';
        let inQuotes = false;
        for (let i = 0; i < text.length; i++) {
            const c = text[i];
            if (inQuotes) {
                if (c === '"') {
                    if (text[i + 1] === '"') { field += '"'; i++; }
                    else { inQuotes = false; }
                } else {
                    field += c;
                }
            } else if (c === '"') {
                inQuotes = true;
            } else if (c === ',') {
                row.push(field); field = '';
            } else if (c === '\\n' || c === '\\r') {
                if (c === '\\r' && text[i + 1] === '\\n') { i++; }
                row.push(field); field = '';
                if (!(row.length === 1 && row[0] === '')) { rows.push(row); }
                row = [];
            } else {
                field += c;
            }
        }
        if (field.length > 0 || row.length > 0) { row.push(field); rows.push(row); }
        return rows;
    }

    function parseCSVToColumns(text) {
        const rows = parseCSV(text);
        if (rows.length < 2) { return null; }
        const header = rows[0].map(h => h.trim());
        const idxName = header.indexOf('Name');
        const idxMedian = header.indexOf('Median Response Time');
        if (idxName === -1 || idxMedian === -1) { return null; }
        const names = [];
        const medians = [];
        for (let r = 1; r < rows.length; r++) {
            const cells = rows[r];
            if (cells.length <= Math.max(idxName, idxMedian)) { continue; }
            const rawName = cells[idxName];
            const parts = rawName.split('|');
            const name = parts[parts.length - 1];
            const median = parseFloat(cells[idxMedian]);
            if (name === undefined || name === '' || Number.isNaN(median)) { continue; }
            names.push(name);
            medians.push(median);
        }
        return { names: names, medians: medians };
    }
"""

REDRAW_JS = """
    function redraw() {
        const nameOrder = [];
        const nameMap = new Map();

        function ingest(store, color) {
            const n = store.data['name'];
            const med = store.data['median'];
            const run = store.data['run'];
            for (let i = 0; i < n.length; i++) {
                const name = n[i];
                if (!nameMap.has(name)) {
                    nameMap.set(name, new Map());
                    nameOrder.push(name);
                }
                nameMap.get(name).set(color, { median: med[i], run: run[i] });
            }
        }

        ingest(run1_store, COLOR_RUN1);
        ingest(run2_store, COLOR_RUN2);

        const factors = [];
        const ys = [];
        const colors = [];
        const runs_col = [];
        const names_col = [];

        for (const name of nameOrder) {
            const m = nameMap.get(name);
            for (const color of [COLOR_RUN1, COLOR_RUN2]) {
                if (m.has(color)) {
                    const entry = m.get(color);
                    factors.push([name, entry.run]);
                    ys.push(entry.median);
                    colors.push(color);
                    runs_col.push(entry.run);
                    names_col.push(name);
                }
            }
        }

        plot_source.data = { x: factors, y: ys, run: runs_col, name: names_col, color: colors };
        x_range.factors = factors;
        plot_source.change.emit();
        x_range.change.emit();
    }
"""

# ---------------------------------------------------------------------------
# Upload widgets + callbacks
#
# Each FileInput gets its own CustomJS. Both callbacks share identical
# parsing/redraw logic (PARSE_CSV_JS + REDRAW_JS); they only differ in
# which hidden store they write to (own_store) and the default filename
# fallback. Colors are fixed per slot: Run 1 is always blue, Run 2 is
# always orange, regardless of which file was uploaded where.
# ---------------------------------------------------------------------------

upload1 = FileInput(accept=".csv", multiple=False)
upload2 = FileInput(accept=".csv", multiple=False)

callback1 = CustomJS(
    args=dict(
        own_store=run1_store,
        other_store=run2_store,
        run1_store=run1_store,
        run2_store=run2_store,
        plot_source=plot_source,
        x_range=x_range,
        COLOR_RUN1=COLOR_RUN1,
        COLOR_RUN2=COLOR_RUN2,
    ),
    code=(
        PARSE_CSV_JS
        + REDRAW_JS
        + """
        if (!cb_obj.value) { return; }
        const text = decodeBase64Utf8(cb_obj.value);
        const parsed = parseCSVToColumns(text);
        if (parsed === null) { return; }
        const filename = cb_obj.filename || 'Run 1';
        own_store.data = {
            name: parsed.names,
            median: parsed.medians,
            run: parsed.names.map(() => filename)
        };
        own_store.change.emit();
        redraw();
        """
    ),
)

callback2 = CustomJS(
    args=dict(
        own_store=run2_store,
        other_store=run1_store,
        run1_store=run1_store,
        run2_store=run2_store,
        plot_source=plot_source,
        x_range=x_range,
        COLOR_RUN1=COLOR_RUN1,
        COLOR_RUN2=COLOR_RUN2,
    ),
    code=(
        PARSE_CSV_JS
        + REDRAW_JS
        + """
        if (!cb_obj.value) { return; }
        const text = decodeBase64Utf8(cb_obj.value);
        const parsed = parseCSVToColumns(text);
        if (parsed === null) { return; }
        const filename = cb_obj.filename || 'Run 2';
        own_store.data = {
            name: parsed.names,
            median: parsed.medians,
            run: parsed.names.map(() => filename)
        };
        own_store.change.emit();
        redraw();
        """
    ),
)

upload1.js_on_change("value", callback1)
upload2.js_on_change("value", callback2)

# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

title_css = "font-size: 2em; font-weight: 600; text-align: center; margin: 10px 0 20px 0;"
subtitle_css = "font-size: 1.3em; font-weight: 500; margin-bottom: 6px;"

header = Div(text=f"<div style='{title_css}'>Performance comparison</div>", sizing_mode="stretch_width")

col1 = column(
    Div(text=f"<div style='{subtitle_css}'>Run 1</div>"),
    upload1,
    sizing_mode="stretch_width",
)
col2 = column(
    Div(text=f"<div style='{subtitle_css}'>Run 2</div>"),
    upload2,
    sizing_mode="stretch_width",
)

uploads_row = row(col1, col2, sizing_mode="stretch_width")

layout = column(
    header,
    uploads_row,
    p,
    sizing_mode="stretch_width",
    margin=(20, 40, 20, 40),
)

output_file("perf_comparison.html", title="Performance comparison")
save(layout, resources=INLINE)
print("Wrote perf_comparison.html")