"""
Define the Figure class that handles all plotting.
"""
import os
from tempfile import NamedTemporaryFile, TemporaryDirectory

try:
    from IPython.display import Image
except ImportError:
    Image = None

from .clib import call_module, APISession
from .base_plotting import BasePlotting
from .utils import build_arg_string
from .decorators import fmt_docstring, use_alias, kwargs_to_strings


def figure(name):
    """
    Start a new figure.

    All plotting commands run afterward will append to this figure.

    Unlike the command-line version (``gmt figure``), this function does not
    trigger the generation of a figure file. An explicit call to
    :func:`gmt.savefig` or :func:`gmt.psconvert` must be made in order to get a
    file.

    Parameters
    ----------
    name : str
        A unique name for this figure. Will use the name to refer to a
        particular figure. You can come back to the figure by calling this
        function with the same name as before.

    """
    # Passing format '-' tells gmt.end to not produce any files.
    fmt = '-'
    with APISession() as session:
        call_module(session, 'figure', '{} {}'.format(name, fmt))


def _unique_name():
    """
    Generate a unique name for a figure.

    Need a unique name for each figure, otherwise GMT will plot everything
    on the same figure instead of creating a new one.

    Returns
    -------
    name : str
        A unique name generated by ``tempfile.NamedTemporaryFile``

    """
    # Use the tempfile module to generate a unique file name.
    tmpfile = NamedTemporaryFile(prefix='gmt-python-', dir=os.path.curdir,
                                 delete=True)
    name = os.path.split(tmpfile.name)[-1]
    tmpfile.close()
    return name


class Figure(BasePlotting):
    """
    Create a GMT figure.

    Use the plotting methods to add elements to the figure.

    Save the output to a file using :meth:`~gmt.Figure.savefig`.
    Insert the figure in a Jupyter notebook using :meth:`~gmt.Figure.show`.
    """

    def __init__(self):
        self._name = _unique_name()

    def _preprocess(self, **kwargs):
        """
        Call the ``figure`` module before each plotting command to ensure we're
        plotting to this particular figure.
        """
        figure(self._name)
        return kwargs

    @fmt_docstring
    @use_alias(F='prefix', T='fmt', A='crop', E='dpi', P='portrait')
    @kwargs_to_strings()
    def psconvert(self, **kwargs):
        """
        Convert [E]PS file(s) to other formats.

        Converts one or more PostScript files to other formats (BMP, EPS, JPEG,
        PDF, PNG, PPM, SVG, TIFF) using GhostScript.

        If no input files are given, will convert the current active figure
        (see :func:`gmt.figure`). In this case, an output name must be given
        using parameter *F*.

        {gmt_module_docs}

        {aliases}

        Parameters
        ----------
        A : str or bool
            Adjust the BoundingBox and HiResBoundingBox to the minimum required
            by the image content. Append ``u`` to first remove any GMT-produced
            time-stamps. Default is True.
        C : str
            Specify a single, custom option that will be passed on to
            GhostScript as is.
        E : int
            Set raster resolution in dpi. Default = 720 for PDF, 300 for
            others.
        F : str
            Force the output file name. By default output names are constructed
            using the input names as base, which are appended with an
            appropriate extension. Use this option to provide a different name,
            but without extension. Extension is still determined automatically.
        I : bool
            Enforce gray-shades by using ICC profiles.
        P : bool
            Force Portrait mode. All Landscape mode plots will be rotated back
            so that they show unrotated in Portrait mode. This is practical
            when converting to image formats or preparing EPS or PDF plots for
            inclusion in documents. Default to True.
        Q : str
            Set the anti-aliasing options for graphics or text. Append the size
            of the subsample box (1, 2, or 4) [4]. Default is no anti-aliasing
            (same as bits = 1).
        T : str
            Sets the output format, where b means BMP, e means EPS, E means EPS
            with PageSize command, f means PDF, F means multi-page PDF, j means
            JPEG, g means PNG, G means transparent PNG (untouched regions are
            transparent), m means PPM, s means SVG, and t means TIFF [default
            is JPEG]. To bjgt you can append - in order to get a grayscale
            image. The EPS format can be combined with any of the other
            formats. For example, ``'ef'`` creates both an EPS and a PDF file.
            The ``'F'`` creates a multi-page PDF file from the list of input PS
            or PDF files. It requires the *F* option.

        """
        kwargs = self._preprocess(**kwargs)
        # Default cropping the figure to True
        if 'A' not in kwargs:
            kwargs['A'] = ''
        # Default portrait mode to True
        if 'P' not in kwargs:
            kwargs['P'] = ''
        with APISession() as session:
            call_module(session, 'psconvert', build_arg_string(kwargs))

    def savefig(self, fname, orientation='portrait', transparent=False,
                crop=True, **kwargs):
        """
        Save the figure to a file.

        This method implements a matplotlib-like interface for
        :meth:`~gmt.Figure.psconvert`.

        Supported formats: PNG (``.png``), JPEG (``.jpg``), PDF (``.pdf``),
        BMP (``.bmp``), TIFF (``.tif``), and EPS (``.eps``).

        You can pass in any keyword arguments that
        :meth:`~gmt.Figure.psconvert` accepts.

        Parameters
        ----------
        fname : str
            The desired figure file name, including the extension. See the list
            of supported formats and their extensions above.
        orientation : str
            Either ``'portrait'`` or ``'landscape'``.
        transparent : bool
            If True, will use a transparent background for the figure. Only
            valid for PNG format.
        crop : bool
            If True, will crop the figure canvas (page) to the plot area.

        """
        # All supported formats
        fmts = dict(png='g', pdf='f', jpg='j', bmp='b', eps='e', tif='t')

        assert orientation in ['portrait', 'landscape'], \
            "Invalid orientation '{}'.".format(orientation)
        portrait = bool(orientation == 'portrait')

        prefix, ext = os.path.splitext(fname)
        ext = ext[1:]  # Remove the .
        assert ext in fmts, "Unknown extension '.{}'".format(ext)
        fmt = fmts[ext]
        if transparent:
            assert ext == 'png', \
                "Transparency unavailable for '{}', only for png.".format(ext)
            fmt = fmt.upper()

        self.psconvert(prefix=prefix, fmt=fmt, crop=crop,
                       portrait=portrait, **kwargs)

    def show(self, dpi=300, width=500):
        """
        Display the figure in the Jupyter notebook.

        You will need to have IPython installed for this to work.
        You should have it if you are using a Jupyter notebook.

        Parameters
        ----------
        dpi : int
            The image resolution (dots per inch).
        width : int
            Width of the figure shown in the notebook in pixels.

        Returns
        -------
        img : IPython.display.Image

        """
        png = self._png_preview(dpi=dpi, anti_alias=True)
        img = Image(data=png, width=width)
        return img

    def _png_preview(self, dpi=70, anti_alias=True):
        """
        Grab a PNG preview of the figure.

        Uses the default parameters from :meth:`~gmt.Figure.savefig`.

        Parameters
        ----------
        dpi : int
            The image resolution (dots per inch).
        anti_alias : bool
            If True, will apply anti-aliasing to the image (using options
            ``Qg=4, Qt=4``).

        Returns
        -------
        png : bytes or ndarray
            The PNG image read as a bytes string.

        """
        savefig_args = dict(dpi=dpi)
        if anti_alias:
            savefig_args['Qg'] = 4
            savefig_args['Qt'] = 4
        with TemporaryDirectory() as tmpdir:
            fname = os.path.join(tmpdir, '{}-preview.png'.format(self._name))
            self.savefig(fname, **savefig_args)
            with open(fname, 'rb') as image:
                png = image.read()
        return png

    def _repr_png_(self):
        """
        Show a PNG preview if the object is returned in an interactive shell.
        For the Jupyter notebook or IPython Qt console.
        """
        return self._png_preview()
