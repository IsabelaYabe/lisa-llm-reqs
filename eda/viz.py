from __future__ import annotations

from typing import Sequence, Optional, Iterable, List, Tuple
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import re

from collections import Counter
from matplotlib import cm
from matplotlib.colors import Colormap
from matplotlib.ticker import MaxNLocator, StrMethodFormatter

_YM_RX = re.compile(r"^\d{4}-\d{2}$")

class Visualizer:
    def __init__(
        self,
        *,
        cmap_name: str = "Wistia",
        figsize: Tuple[int, int] = (10, 6),
        grid: bool = True,
        value_label_fmt: str = "{:}",
        title_fontsize: int = 14,
        label_fontsize: int = 11,
        data_format: Optional[str] = _YM_RX
    ):
        self.cmap_name = cmap_name
        self.figsize = figsize
        self.grid = grid
        self.value_label_fmt = value_label_fmt
        self.title_fontsize = title_fontsize
        self.label_fontsize = label_fontsize
        self.data_format = data_format

    def _colors(self, 
        n: int, 
        cmap_name: Optional[str] = None
        ) -> np.ndarray:
        """
        Generate n distinct colors from the colormap.
        """
        cmap = cm.get_cmap(cmap_name or self.cmap_name)
        return cmap(np.linspace(0, 1, n))

    def _colors_by_values(self,
        values: Sequence[float],
        *,
        round_ndigits: Optional[int] = None,
        cmap_name: Optional[str] = None,
        ) -> list:
        """
        Assign colors to values, grouping identical (or rounded) values to the same color.
        """
        vals = list(values)
        if round_ndigits is not None:
            vals = [round(v, round_ndigits) for v in vals]
        uniq = sorted(set(vals))
        cmap = self._colors(len(uniq), cmap_name)
        lut = {v: c for v, c in zip(uniq, cmap)}
        return [lut[v] for v in vals]

    def _apply_common(self, 
        *, 
        xlabel: Optional[str] = None,
        ylabel: Optional[str] = None, title: Optional[str] = None
        ):
        """
        Applies common settings to the current plot.
        """
        if xlabel: 
            plt.xlabel(xlabel, fontsize=self.label_fontsize)
        if ylabel: 
            plt.ylabel(ylabel, fontsize=self.label_fontsize)
        if title:  
            plt.title(title, fontsize=self.title_fontsize, fontweight="bold")
        if self.grid: 
            plt.grid(axis="both", linestyle="--", alpha=0.5)
        plt.tight_layout()
    
    @staticmethod
    def _looks_year_month(seq) -> bool:
        """
        Checks if the sequence looks like year-month strings (e.g., "2023-01").
        """
        if not seq:
            return False
        return all(isinstance(s, str) and _YM_RX.match(s) for s in seq)
    
    @staticmethod
    def _is_int_sequence(seq: Sequence) -> bool:
        """
        Checks if the sequence contains only integers (or can be safely converted to integers).
        """
        arr = np.asarray(list(seq))
        if arr.size == 0:
            return False

        if np.issubdtype(arr.dtype, np.integer):
            return True

        return (np.issubdtype(arr.dtype, np.integer)
        or np.all(np.isfinite(arr) & (np.abs(arr - np.round(arr)) < 1e-9)))

    def barh(self,
        labels: Sequence[str],
        values: Sequence[float | int],
        *,
        title: str = "Horizontal Bar Chart",
        xlabel: str = "Value",
        annotate: bool = True,
        cmap_name: Optional[str] = None,
        ):
        """
        Horizontal bar chart with optional value annotations.
        """
        labels = list(labels)
        values = list(values)
        if not values:
            return
        
        are_all_int = all(isinstance(v, int) or (isinstance(v, float) and v.is_integer()) for v in values)
        if are_all_int:
            format_str = "{:.0f}" 
        else:
            format_str = self.value_label_fmt
        
        colors = self._colors_by_values(values, cmap_name=cmap_name)
        fig, ax = plt.subplots(figsize=self.figsize)
        bars = plt.barh(labels[::-1], values[::-1], color=colors[::-1])
        if annotate:
            dx = (max(values) if values else 1) * 0.01 + 0.02
            for bar, val in zip(bars, values[::-1]):
                ax.text(bar.get_width() + dx,
                         bar.get_y() + bar.get_height()/2,
                         format_str.format(val),
                         va="center", 
                         ha="left", 
                         fontsize=10, 
                         color="black")
        self._apply_common(xlabel=xlabel, title=title)
        plt.show()

    def barv(self, 
        labels: Sequence[str], 
        values: Sequence[float | int], 
        *, 
        title: str = "Vertical Bar Chart", 
        ylabel: str = "Value", 
        annotate: bool = True, 
        rotation: int = 0,
        cmap_name: Optional[str] = None,):
        """
        Vertical bar chart with optional value annotations.
        """
        labels = list(labels)
        values = list(values)
        if not values:
            return

        are_all_int = all(isinstance(v, int) or (isinstance(v, float) and float(v).is_integer()) for v in values)
        format_str = "{:.0f}" if are_all_int else self.value_label_fmt

        colors = self._colors_by_values(values, cmap_name=cmap_name)
        fig, ax = plt.subplots(figsize=self.figsize)
        bars = ax.bar(labels, values, color=colors)

        if annotate:
            dy = (max(values) if values else 1) * 0.01 + 0.02
            for bar, val in zip(bars, values):
                ax.text(bar.get_x() + bar.get_width()/2,
                        bar.get_height() + dy,
                        format_str.format(val),
                        va="bottom", ha="center", fontsize=10, color="black")

        if are_all_int:
            ax.yaxis.set_major_locator(MaxNLocator(integer=True))
            ax.yaxis.set_major_formatter(StrMethodFormatter('{x:.0f}'))

        plt.xticks(rotation=rotation)
        self._apply_common(ylabel=ylabel, title=title)
        plt.show()

    def histogram(self, 
        data: Sequence[float | int], 
        *, 
        bins: int = 20, 
        bin_method: str = "auto", 
        title: str = "Histogram", 
        xlabel: str = "Value", 
        ylabel: str = "Frequency",
        density: bool = False,
        annotate: bool = True,
        cmap_name: Optional[str] = None):
        """
        Plot a histogram of the data.
        """
        arr = np.asarray(list(data), dtype=float)
        arr = arr[np.isfinite(arr)]
        if arr.size == 0:
            return
        
        if bins is None:
            edges = np.histogram_bin_edges(arr, bins=bin_method)
        else:
            edges = bins

        colors = self._colors(1, cmap_name)[0]
        fig, ax = plt.subplots(figsize=self.figsize)

        n, be, patches = ax.hist(arr, bins=edges, color=colors, edgecolor="black", density=density)
        fmt = "{:.2f}" if density else "{:.0f}"

        if annotate:
            ymax = np.max(n) if n.size else 0
            dy = (ymax * 0.01) + (0.02 if ymax == 0 else 0.0)
            for rect, val in zip(patches, n):
                x = rect.get_x() + rect.get_width() / 2
                y = rect.get_height()
                ax.text(x, y + dy, fmt.format(val), ha="center", va="bottom", fontsize=10, color="black")
        
        if not density:
            ax.yaxis.set_major_locator(MaxNLocator(integer=True))
            ax.yaxis.set_major_formatter(StrMethodFormatter('{x:.0f}'))

        self._apply_common(xlabel=xlabel, ylabel=ylabel, title=title)
        plt.show()

    def boxplot(self,
        data: Iterable[Sequence[float | int]] | Sequence[float | int],
        *,
        labels: Optional[Sequence[str]] = None,
        title: str = "Boxplot",
        ylabel: str = "Value",
        cmap_name: Optional[str] = None):
        """
        Plot a boxplot for one or more datasets.
        """
        plt.figure(figsize=self.figsize)
        bp = plt.boxplot(data, patch_artist=True, labels=labels)
        colors = self._colors(len(bp["boxes"]), cmap_name)
        for patch, c in zip(bp["boxes"], colors):
            patch.set_facecolor(c)
        self._apply_common(ylabel=ylabel, title=title)
        plt.show()

    def heatmap(self, 
            M: pd.DataFrame | np.ndarray, 
            *,
            xlabels: Optional[Sequence[str]] = None,
            ylabels: Optional[Sequence[str]] = None,
            title: str = "Heatmap",
            xlabel: str = "", 
            ylabel: str = "",
            annotate: bool = True, 
            fmt: str = ".0f",
            cmap_name: Optional[str] = None):
        """
        Heatmap from a 2D array or DataFrame, with optional annotations.
        """
        if isinstance(M, pd.DataFrame):
            if xlabels is None:
                xlabels = list(M.columns) 
            if ylabels is None:
                ylabels = list(M.index)
            M = M.values

        cmap = cm.get_cmap(cmap_name or self.cmap_name)
        fig, ax = plt.subplots(figsize=self.figsize)
        im = plt.imshow(M, aspect="auto", interpolation="nearest", cmap=cmap_name)
        fig.colorbar(im, ax=ax)

        if xlabels is not None:
            ax.set_xticks(range(len(xlabels)))
            ax.set_xticklabels(xlabels, rotation=90, fontsize=self.label_fontsize)
        if ylabels is not None:
            ax.set_yticks(range(len(ylabels)))
            ax.set_yticklabels(ylabels, fontsize=self.label_fontsize)

        if annotate:
            for i in range(M.shape[0]):
                for j in range(M.shape[1]):
                    v = M[i, j]
                    if v != 0:
                        plt.text(j, i, format(v, fmt), ha="center", va="center", fontsize=8, color="black")

        self._apply_common(xlabel=xlabel, ylabel=ylabel, title=title)
        plt.show()

    def line(self,
            x: Sequence,
            y: Sequence[int | float | str],
            *,
            title: str = "Line Chart",
            xlabel: str = "X",
            ylabel: str = "Y",
            marker: Optional[str] = "o",
            rotation: int = 0,
            cmap_name: Optional[str] = None,
            aggregate: str = "sum",   # 'sum', 'mean', 'count'
            sort_x: bool = True):
        """
        Line chart.
        If x is in the format YYYY-MM, uses a monthly time axis with formatting '%Y-%m'.
        y must be numeric (numeric strings are converted).
        """
        x_list = list(x)
        y_raw = list(y)
        y_num = pd.to_numeric(y_raw, errors="raise").tolist()

        color = self._colors(1, cmap_name)[0]
        fig, ax = plt.subplots(figsize=self.figsize)

        if self._looks_year_month(x_list):
            df = pd.DataFrame({"ym": x_list, "y": y_num})
            if sort_x:
                dt = pd.to_datetime(df["ym"], format="%Y-%m")
                df = df.assign(dt=dt).sort_values("dt")
            else:
                df = df.assign(dt=pd.to_datetime(df["ym"], format="%Y-%m"))
            if aggregate:
                aggfunc = {"sum": np.sum, "mean": np.mean, "max": np.max, "min": np.min}.get(aggregate, np.sum)
                df = df.groupby("dt", as_index=False)["y"].agg(aggfunc)

            ax.plot(df["dt"], df["y"], marker=marker, color=color)
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))

            if rotation:
                for lab in ax.get_xticklabels():
                    lab.set_rotation(rotation)
                    lab.set_horizontalalignment("right")
            if self._is_int_sequence(df["y"].to_numpy()):
                ax.yaxis.set_major_locator(MaxNLocator(integer=True))
                ax.yaxis.set_major_formatter(StrMethodFormatter('{x:.0f}'))
        else:
            ax.plot(x_list, y_num, marker=marker, color=color)
            if self._is_int_sequence(x_list):
                ax.xaxis.set_major_locator(MaxNLocator(integer=True))
                ax.xaxis.set_major_formatter(StrMethodFormatter('{x:.0f}'))
            if self._is_int_sequence(y_num):
                ax.yaxis.set_major_locator(MaxNLocator(integer=True))
                ax.yaxis.set_major_formatter(StrMethodFormatter('{x:.0f}'))
            if rotation:
                plt.xticks(rotation=rotation)

        self._apply_common(xlabel=xlabel, ylabel=ylabel, title=title)
        plt.tight_layout()
        plt.show()

    def stats_table(
        self,
        data: Sequence[float | int],
        *,
        percentiles: Sequence[float] = (0.25, 0.5, 0.75),
        floatfmt: str = "{:.3f}",
        title: str = "Statistical Summary",
    ) -> pd.DataFrame:
        """
        Displays a table with basic statistics for:
        - a single sequence (list, Series, ndarray)
        - or a dict of sequences (multi-colunas).
        Returns the DataFrame with stats.
        """
        if isinstance(data, dict):
            dfc = pd.DataFrame(data)
        elif isinstance(data, pd.Series):
            dfc = data.to_frame(name=data.name or "values")
        else:
            dfc = pd.DataFrame({"values": list(data)})

        desc = dfc.describe(percentiles=percentiles).T  
        return desc 
