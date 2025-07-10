import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd



def plot_price_trend(df: pd.DataFrame, price_col: str = 'Close', title: str = "Price Trend",
                     scale: str = 'Linear', additional_lines: list = None, figsize: tuple = (15, 7)):
    """

    :param df:
    :param price_col:
    :param title:
    :param scale:
    :param additional_lines:
    :param figsize:
    :return:
    """
    plt.figure(figsize=figsize)
    plt.plot(df.index, df[price_col], label=price_col, color='blue', alpha=0.8)

    if additional_lines:
        for line_info in additional_lines:
            col = line_info.get('col')
            label = line_info.get('label', col)
            color = line_info.get('color', 'black')
            linestyle = line_info.get('linestyle', '-')
            if col in df.columns:
                plt.plot(df.index, df[col], label=label, color=color, linestyle=linestyle, alpha=0.7)

    if scale == 'log':
        plt.yscale('log')
        plt.ylabel(f'{price_col} (Log Scale)')
    else:
        plt.ylabel(f'{price_col} (USD)')

    plt.title(title, fontsize=16)
    plt.xlabel('Date', fontsize=12)
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()

def plot_volume_trend(df: pd.DataFrame, volume_col: str = 'Volume', title: str = 'Trading Volume Over Time',
                      figsize: tuple = (15, 7)):
    """

    :param df:
    :param volume_col:
    :param title:
    :param figsize:
    :return:
    """
    plt.figure(figsize=figsize)
    plt.plot(df.index, df[volume_col], label=volume_col, color='orange', alpha=0.7)
    plt.title(title, fontsize=16)
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Volume', fontsize=12)
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()

def plot_correlation_heatmap(df: pd.DataFrame, columns: list, title: str = 'Correlation Matrix',
                             figsize: tuple = (12,10)):
    """

    :param df:
    :param columns:
    :param title:
    :param figsize:
    :return:
    """
    df_corr = df[columns].dropna()

    plt.figure(figsize=figsize)
    sns.heatmap(df_corr.corr(), annot=True, cmap='coolwarm', fmt='.2f', linewidths=.5)
    plt.title(title, fontsize=16)
    plt.tight_layout()
    plt.show()

def plot_returns_histogram(df: pd.DataFrame, returns_col: str = 'Log_Returns', bins: int = 100,
                           title: str = 'Distribution of Daily Returns', figsize: tuple = (10, 6)):
    """

    :param df:
    :param returns_col:
    :param bins:
    :param title:
    :param figsize:
    :return:
    """
    plt.figure(figsize=figsize)
    sns.histplot(df[returns_col].dropna(), bins=bins, kde=True, color='skyblue')
    plt.title(title, fontsize=16)
    plt.xlabel('Returns', fontsize=12)
    plt.ylabel('Frequency', fontsize=12)
    plt.grid(True)
    plt.tight_layout()
    plt.show()

def plot_distribution(df: pd.DataFrame, col: str, bins: int = 50, title: str = "Distribution",
                      color: str = 'grey', figsize: tuple = (10, 6)):
    """

    :param df:
    :param col:
    :param bins:
    :param title:
    :param color:
    :param figsize:
    :return:
    """
    plt.figure(figsize=figsize)
    sns.histplot(df[col].dropna(), bins=bins, kde=True, color=color)
    plt.title(title, fontsize=16)
    plt.xlabel(col, fontsize=12)
    plt.ylabel('Frequency', fontsize=12)
    plt.grid(True)
    plt.tight_layout()
    plt.show()