from __future__ import annotations

from typing import Sequence, Optional, Iterable, List, Tuple
import numpy as np
import pandas as pd
from collections import Counter
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.colors import Colormap

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
    ):
        self.cmap_name = cmap_name
        self.figsize = figsize
        self.grid = grid
        self.value_label_fmt = value_label_fmt
        self.title_fontsize = title_fontsize
        self.label_fontsize = label_fontsize

    def _colors(self, n: int) -> np.ndarray:
        cmap: Colormap = cm.get_cmap(self.cmap_name)
        return cmap(np.linspace(0, 1, n))
    
    def _apply_common(self, 
        *, 
        xlabel: str | None = None, 
        ylabel: str | None = None, 
        title: str | None = None):
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

    def barh(self, 
        labels: Sequence[str], 
        values: Sequence[float], 
        *, 
        title: str = "Horizontal Bar Chart", 
        xlabel: str = "Value", 
        annotate: bool = True):
        """
        Horizontal bar chart with optional value annotations.
        """
        labels = list(labels)
        values = list(values)
        colors = self._colors(len(values))
        plt.figure(figsize=self.figsize)
        bars = plt.barh(labels[::-1], values[::-1], color=colors[::-1])
        if annotate:
            for bar, val in zip(bars, values[::-1]):
                plt.text(
                    bar.get_width() + max(values)*0.01,
                    bar.get_y() + bar.get_height()/2,
                    self.value_label_fmt.format(val),
                    va="center", 
                    ha="left", 
                    fontsize=10, 
                    color="black"
                    )
        self._apply_common(xlabel=xlabel, title=title)
        plt.show()

    def barv(self, 
        labels: Sequence[str], 
        values: Sequence[float], 
        *, 
        title: str = "Vertical Bar Chart", 
        ylabel: str = "Value", 
        annotate: bool = True, 
        rotation: int = 0):
        """
        Vertical bar chart with optional value annotations.
        """
        labels = list(labels)
        values = list(values)
        colors = self._colors(len(values))
        plt.figure(figsize=self.figsize)
        bars = plt.bar(labels, values, color=colors)
        if annotate:
            for bar, val in zip(bars, values):
                plt.text(
                    bar.get_x() + bar.get_width()/2,
                    bar.get_height() + max(values)*0.01,
                    self.value_label_fmt.format(val),
                    va="bottom", 
                    ha="center", 
                    fontsize=10, 
                    color="black"
                    )
        
        plt.xticks(rotation=rotation)
        self._apply_common(ylabel=ylabel, title=title)
        plt.show()

    def histogram(self, 
        data: Sequence[float], 
        *, 
        bins: int = 20, 
        title: str = "Histogram", 
        xlabel: str = "Value", 
        density: bool = False):
        """
        Plot a histogram of the data.
        """
        colors = self._colors(1)
        plt.figure(figsize=self.figsize)
        plt.hist(data, bins=bins, color=colors[0], edgecolor="black", density=density)
        self._apply_common(xlabel=xlabel, title=title)
        plt.show()

    def boxplot(self,
        data: Iterable[Sequence[float]] | Sequence[float],
        *,
        labels: Optional[Sequence[str]] = None,
        title: str = "Boxplot",
        ylabel: str = "Value"):
        """
        Plot a boxplot for one or more datasets.
        """
        plt.figure(figsize=self.figsize)
        bp = plt.boxplot(data, patch_artist=True, labels=labels)
        colors = self._colors(len(bp["boxes"]))
        for patch, c in zip(bp["boxes"], colors):
            patch.set_facecolor(c)
        self._apply_common(ylabel=ylabel, title=title)
        plt.show()

    def heatmap(self, 
        M: pd.DataFrame | np.ndarray,*, 
        xlabels: Optional[Sequence[str]] = None,
        ylabels: Optional[Sequence[str]] = None,title: str = "Heatmap", 
        xlabel: str = "", 
        ylabel: str = ""):
        """
        Plot a heatmap from a 2D numpy array or DataFrame.
        """
        if isinstance(M, pd.DataFrame):
            xlabels = list(M.columns) if xlabels is None else xlabels
            ylabels = list(M.index)   if ylabels is None else ylabels
            M = M.values
        plt.figure(figsize=self.figsize)
        plt.imshow(M, aspect="auto", interpolation="nearest", cmap=self.cmap_name,
           vmin=0 if np.issubdtype(np.array(M).dtype, np.floating) else None,
           vmax=1 if np.issubdtype(np.array(M).dtype, np.floating) else None)

        plt.colorbar()
        if xlabels is not None:
            plt.xticks(range(len(xlabels)), xlabels, rotation=90)
        if ylabels is not None:
            plt.yticks(range(len(ylabels)), ylabels)
        self._apply_common(xlabel=xlabel, ylabel=ylabel, title=title)
        plt.show()
    
    def heatmap_from_df(self,
        df: pd.DataFrame,
        col_x: str,
        col_y: str,
        *,
        aggfunc: str | callable = "size",
        normalize: bool = False,
        title: str | None = None,
        xlabel: str | None = None,
        ylabel: str | None = None):
        """
        Creates a heatmap from two columns of a DataFrame.
        """
        pivot = pd.pivot_table(df[col_y], df[col_x], aggfunc=aggfunc)

        if normalize:
            pivot = pivot.div(pivot.sum().sum())

        return self.heatmap(
            pivot,
            xlabels=pivot.columns,
            ylabels=pivot.index,
            title=title or f"Heatmap: {col_y} × {col_x}",
            xlabel=xlabel or col_x,
            ylabel=ylabel or col_y,
        )

    def heatmap_cooccurrence_from_listcol(
        self,
        df: pd.DataFrame,
        list_col: str = "keywords_norm",
        *,
        top_n: int | None = 50,
        normalize: bool = False,
        title: str | None = None,
    ):
        """
        Builds a co-occurrence matrix from a column of lists.
        Keeps the top_n most frequent labels (if defined).
        """
        items = []
        for x in df.get(list_col, []):
            if isinstance(x, (list, tuple, set)):
                items.extend(x)
        freq = Counter(items)
        labels = [k for k, _ in (freq.most_common(top_n) if top_n else freq.most_common())]
        idx = {k: i for i, k in enumerate(labels)}

        if not labels:
            return

        M = np.zeros((len(labels), len(labels)), dtype=float)
        for x in df.get(list_col, []):
            if not isinstance(x, (list, tuple, set)):
                continue
            xs = [t for t in x if t in idx]
            for i in range(len(xs)):
                for j in range(i + 1, len(xs)):
                    a, b = idx[xs[i]], idx[xs[j]]
                    M[a, b] += 1
                    M[b, a] += 1

        if normalize and M.sum() > 0:
            M = M / M.sum()

        pivot = pd.DataFrame(M, index=labels, columns=labels)
        return self.heatmap(
            pivot,
            xlabels=labels,
            ylabels=labels,
            title=title or f"Co-occurrence ({list_col})",
            xlabel=list_col,
            ylabel=list_col,
        )

    def line(self,
        x: Sequence,
        y: Sequence[float],
        *,
        title: str = "Line Chart",
        xlabel: str = "X",
        ylabel: str = "Y",
        marker: Optional[str] = "o"):
        """
        Simple line chart with optional markers.
        """
        colors = self._colors(1)
        plt.figure(figsize=self.figsize)
        plt.plot(x, y, marker=marker, color=colors[0])
        self._apply_common(xlabel=xlabel, ylabel=ylabel, title=title)
        plt.show()

    def area(self,
        X: Sequence,
        Y: Sequence[float] | np.ndarray,
        *,
        stacked: bool = False,
        labels: Optional[Sequence[str]] = None,
        title: str = "Area Chart",
        xlabel: str = "X",
        ylabel: str = "Y"):
        """
        Area chart, stacked if multiple series are provided.
        """
        plt.figure(figsize=self.figsize)
        if stacked and isinstance(Y, (list, tuple)) and labels:
            Y = np.array(Y)
            colors = self._colors(Y.shape[0])
            for i, row in enumerate(Y):
                plt.fill_between(
                    X, 
                    row if i==0 else row + Y[:i].sum(axis=0),
                    Y[:i].sum(axis=0) if i>0 else 0,
                    color=colors[i], 
                    alpha=0.8, 
                    label=labels[i]
                    )
            plt.legend()
        else:
            colors = self._colors(1)
            plt.fill_between(X, Y, color=colors[0], alpha=0.8)
        self._apply_common(xlabel=xlabel, ylabel=ylabel, title=title)
        plt.show()

    def chord(self, 
        M: np.ndarray | pd.DataFrame, 
        labels: Optional[Sequence[str]] = None,
        *, 
        title: str = "Chord Diagram", 
        min_weight: float = 0.0):
        """
        Draws simple chords from a symmetric connection matrix (NxN).
        """
        if isinstance(M, pd.DataFrame):
            if labels is None:
                labels = list(M.index)
            M = M.values
        n = M.shape[0]
        theta = np.linspace(0, 2*np.pi, n, endpoint=False)
        node_xy = np.c_[np.cos(theta), np.sin(theta)]
        norm = M / (M.max() if M.max() > 0 else 1)

        plt.figure(figsize=self.figsize)
        plt.scatter(node_xy[:,0], node_xy[:,1], s=400, c=self._colors(n))
        if labels:
            for (x,y), lab in zip(node_xy, labels):
                plt.text(1.08*x, 1.08*y, lab, ha="center", va="center", fontsize=9)

        for i in range(n):
            for j in range(i+1, n):
                w = norm[i, j]
                if w <= min_weight: 
                    continue
                x1, y1 = node_xy[i]; x2, y2 = node_xy[j]
                t = np.linspace(0, 1, 100)
                ctrl = 0.6
                cx, cy = ctrl*(x1+x2)/2, ctrl*(y1+y2)/2
                xs = (1-t)**2*x1 + 2*(1-t)*t*cx + t**2*x2
                ys = (1-t)**2*y1 + 2*(1-t)*t*cy + t**2*y2
                plt.plot(xs, ys, color=cm.get_cmap(self.cmap_name)(w), alpha=0.8, linewidth=1+3*w)

        plt.axis("off")
        plt.title(title, fontsize=self.title_fontsize, fontweight="bold")
        plt.tight_layout()
        plt.show()