from __future__ import annotations

from typing import TYPE_CHECKING

from ..._settings import settings

if TYPE_CHECKING:
    from collections.abc import Collection, Sequence
    from typing import Any, Literal

    import numpy as np
    import pandas as pd
    from anndata import AnnData


def mnn_correct(  # noqa: PLR0913
    *datas: AnnData | np.ndarray,
    var_index: Collection[str] | None = None,
    var_subset: Collection[str] | None = None,
    batch_key: str = "batch",
    index_unique: str = "-",
    batch_categories: Collection[Any] | None = None,
    k: int = 20,
    sigma: float = 1.0,
    cos_norm_in: bool = True,
    cos_norm_out: bool = True,
    svd_dim: int | None = None,
    var_adj: bool = True,
    compute_angle: bool = False,
    mnn_order: Sequence[int] | None = None,
    svd_mode: Literal["svd", "rsvd", "irlb"] = "rsvd",
    do_concatenate: bool = True,
    save_raw: bool = False,
    n_jobs: int | None = None,
    **kwargs,
) -> tuple[
    np.ndarray | AnnData,
    list[pd.DataFrame],
    list[tuple[float | None, int]] | None,
]:
    """Correct batch effects by matching mutual nearest neighbors :cite:p:`Haghverdi2018` :cite:p:`Kang2018`.

    This uses the implementation of mnnpy_ :cite:p:`Kang2018`.

    Depending on `do_concatenate`, returns matrices or `AnnData` objects in the
    original order containing corrected expression values or a concatenated
    matrix or AnnData object.

    Be reminded that it is not advised to use the corrected data matrices for
    differential expression testing.

    More information and bug reports `here <mnnpy>`__.

    .. _mnnpy: https://github.com/chriscainx/mnnpy

    Parameters
    ----------
    datas
        Expression matrices or AnnData objects. Matrices should be shaped like
        n_obs × n_vars (n_cell × n_gene) and have consistent number of columns.
        AnnData objects should have same number of variables.
    var_index
        The index (list of str) of vars (genes). Necessary when using only a
        subset of vars to perform MNN correction, and should be supplied with
        `var_subset`. When `datas` are AnnData objects, `var_index` is ignored.
    var_subset
        The subset of vars (list of str) to be used when performing MNN
        correction. Typically, a list of highly variable genes (HVGs).
        When set to `None`, uses all vars.
    batch_key
        The `batch_key` for :meth:`~anndata.AnnData.concatenate`.
        Only valid when `do_concatenate` and supplying `AnnData` objects.
    index_unique
        The `index_unique` for :meth:`~anndata.AnnData.concatenate`.
        Only valid when `do_concatenate` and supplying `AnnData` objects.
    batch_categories
        The `batch_categories` for :meth:`~anndata.AnnData.concatenate`.
        Only valid when `do_concatenate` and supplying AnnData objects.
    k
        Number of mutual nearest neighbors.
    sigma
        The bandwidth of the Gaussian smoothing kernel used to compute the
        correction vectors. Default is 1.
    cos_norm_in
        Whether cosine normalization should be performed on the input data prior
        to calculating distances between cells.
    cos_norm_out
        Whether cosine normalization should be performed prior to computing corrected expression values.
    svd_dim
        The number of dimensions to use for summarizing biological substructure
        within each batch. If None, biological components will not be removed
        from the correction vectors.
    var_adj
        Whether to adjust variance of the correction vectors. Note this step
        takes most computing time.
    compute_angle
        Whether to compute the angle between each cell’s correction vector and
        the biological subspace of the reference batch.
    mnn_order
        The order in which batches are to be corrected. When set to None, datas
        are corrected sequentially.
    svd_mode
        `'svd'` computes SVD using a non-randomized SVD-via-ID algorithm,
        while `'rsvd'` uses a randomized version. `'irlb'` perfores
        truncated SVD by implicitly restarted Lanczos bidiagonalization
        (forked from https://github.com/airysen/irlbpy).
    do_concatenate
        Whether to concatenate the corrected matrices or AnnData objects. Default is True.
    save_raw
        Whether to save the original expression data in the
        :attr:`~anndata.AnnData.raw` attribute.
    n_jobs
        The number of jobs. When set to `None`, automatically uses
        :attr:`scanpy.settings.n_jobs`.
    kwargs
        optional keyword arguments for irlb.

    Returns
    -------
    datas
        Corrected matrix/matrices or AnnData object/objects, depending on the
        input type and `do_concatenate`.
    mnn_list
        A list containing MNN pairing information as DataFrames in each iteration step.
    angle_list
        A list containing angles of each batch.

    """
    if len(datas) < 2:
        return datas, [], []

    try:
        import mnnpy
        from mnnpy import mnn_correct
    except ImportError as e:
        msg = "Please install the package mnnpy (https://github.com/chriscainx/mnnpy). "
        raise ImportError(msg) from e

    n_jobs = settings.n_jobs if n_jobs is None else n_jobs

    if n_jobs < 2:
        mnnpy.settings.normalization = "single"
    else:
        mnnpy.settings.normalization = "parallel"

    datas, mnn_list, angle_list = mnn_correct(
        *datas,
        var_index=var_index,
        var_subset=var_subset,
        batch_key=batch_key,
        index_unique=index_unique,
        batch_categories=batch_categories,
        k=k,
        sigma=sigma,
        cos_norm_in=cos_norm_in,
        cos_norm_out=cos_norm_out,
        svd_dim=svd_dim,
        var_adj=var_adj,
        compute_angle=compute_angle,
        mnn_order=mnn_order,
        svd_mode=svd_mode,
        do_concatenate=do_concatenate,
        save_raw=save_raw,
        n_jobs=n_jobs,
        **kwargs,
    )
    return datas, mnn_list, angle_list
