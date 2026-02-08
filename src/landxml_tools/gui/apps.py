"""
Aplicaciones embebibles de LandXML Tools.
Contiene las clases GUI principales que pueden usarse en la suite o standalone.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import os
import sys

# Asegurar que el path sea correcto para importaciones internas si se lanza standalone
try:
    from ..io.landxml import parse_landxml_surface
    from ..processing.raster import rasterize_surface_tin
    from ..viz.plotting import create_colormap_legend, save_colored_map
    from ..io.export import save_geotiff, save_world_file
    from .theme import COLORS, FONTS, SPACING
    from .widgets import (
        ModernButton, FileSelector, ConfigRow, ToolTip,
        Card, StyledCheckbox, center_window
    )
except ImportError:
    # Esto permite que el IDE reconozca los imports cuando se edita el archivo
    from landxml_tools.io.landxml import parse_landxml_surface
    from landxml_tools.processing.raster import rasterize_surface_tin
    from landxml_tools.viz.plotting import create_colormap_legend, save_colored_map
    from landxml_tools.io.export import save_geotiff, save_world_file
    from landxml_tools.gui.theme import COLORS, FONTS, SPACING
    from landxml_tools.gui.widgets import (
        ModernButton, FileSelector, ConfigRow, ToolTip,
        Card, StyledCheckbox, center_window
    )

class LandXMLImageGUI:
    """
    Interfaz gráfica para visualizar superficies LandXML como imágenes rasterizadas.
    """
    def __init__(self, parent):
        self.parent = parent
        self.root = parent
        self.is_standalone = isinstance(parent, (tk.Tk, tk.Toplevel))

        if self.is_standalone:
            self.parent.title("LandXML to Image")
            self.parent.geometry("540x780")
            self.parent.configure(bg=COLORS['bg_light'])
            center_window(self.parent)
        
        self.file_path = tk.StringVar()
        self.resolution_var = tk.StringVar(value="0.05")
        self.epsg_var = tk.StringVar(value="25830")
        self.output_name_var = tk.StringVar(value="superficie")
        self.colormap_var = tk.StringVar(value="terrain")
        self.whitening_var = tk.IntVar(value=0)
        self.save_png_var = tk.BooleanVar(value=True)
        self.save_jpg_var = tk.BooleanVar(value=True)
        self.save_tiff_var = tk.BooleanVar(value=True)
        self.save_legend_var = tk.BooleanVar(value=True)
        self.classify_var = tk.BooleanVar(value=True)
        self.class_interval_var = tk.StringVar(value="1.00")
        self.output_dir_var = tk.StringVar(value="")
        self.processing = False
        
        self._create_ui()
    
    def _create_ui(self):
        main = tk.Frame(self.parent, bg=COLORS['bg_light'])
        main.pack(fill=tk.BOTH, expand=True, padx=SPACING['xl'], pady=SPACING['lg'])
        
        files_card = Card(main, "Archivo de Entrada")
        self.file_selector = FileSelector(files_card.content, "Superficie LandXML",
                                           self.file_path, on_select=self._on_file_selected)
        self.file_selector.pack(fill=tk.X)
        
        config_card = Card(main, "Parámetros")
        params_grid = tk.Frame(config_card.content, bg=COLORS['bg_white'])
        params_grid.pack(fill=tk.X)
        ConfigRow(params_grid, "Resolución (m):", self.resolution_var, 8).grid(row=0, column=0, sticky='w', pady=SPACING['xs'])
        ConfigRow(params_grid, "Código EPSG:", self.epsg_var, 8).grid(row=0, column=1, sticky='w', pady=SPACING['xs'], padx=(SPACING['lg'], 0))
        ConfigRow(params_grid, "Nombre salida:", self.output_name_var, 16).grid(row=1, column=0, columnspan=2, sticky='w', pady=SPACING['xs'])
            
        colormap_row = tk.Frame(config_card.content, bg=COLORS['bg_white'])
        colormap_row.pack(fill=tk.X, pady=SPACING['xs'])
        tk.Label(colormap_row, text="Mapa de color:", font=FONTS['body'], width=16, anchor='w', bg=COLORS['bg_white'], fg=COLORS['text_secondary']).pack(side=tk.LEFT)
        self.colormap_combo = ttk.Combobox(colormap_row, textvariable=self.colormap_var, font=FONTS['body'], width=14, state='readonly')
        self.colormap_combo['values'] = ('terrain', 'gist_earth', 'YlOrBr', 'copper', 'viridis', 'plasma', 'inferno', 'magma', 'cividis')
        self.colormap_combo.pack(side=tk.LEFT)
        self.preview_label = tk.Label(colormap_row, bg=COLORS['bg_white'], width=150, height=20)
        self.preview_label.pack(side=tk.LEFT, padx=(SPACING['sm'], 0))
        self.colormap_combo.bind("<<ComboboxSelected>>", self._update_colormap_preview)
        
        whiten_row = tk.Frame(config_card.content, bg=COLORS['bg_white'])
        whiten_row.pack(fill=tk.X, pady=(SPACING['xs'], 0))
        tk.Label(whiten_row, text="Blanqueamiento (%):", font=FONTS['body'], width=16, anchor='w', bg=COLORS['bg_white'], fg=COLORS['text_secondary']).pack(side=tk.LEFT)
        whiten_controls = tk.Frame(whiten_row, bg=COLORS['bg_white'])
        whiten_controls.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.whiten_scale = tk.Scale(whiten_controls, from_=0, to=100, orient=tk.HORIZONTAL, variable=self.whitening_var, length=250, bg=COLORS['bg_white'], highlightthickness=0, font=FONTS['small'], showvalue=0, command=lambda v: self._update_colormap_preview())
        self.whiten_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.whiten_spin = tk.Spinbox(whiten_controls, from_=0, to=100, textvariable=self.whitening_var, width=5, font=FONTS['body'], command=self._update_colormap_preview)
        self.whiten_spin.pack(side=tk.LEFT, padx=(SPACING['sm'], 0))
        self._update_colormap_preview()
        
        dir_row = tk.Frame(config_card.content, bg=COLORS['bg_white'])
        dir_row.pack(fill=tk.X, pady=(SPACING['sm'], 0))
        tk.Label(dir_row, text="Directorio salida:", font=FONTS['body'], width=16, anchor='w', bg=COLORS['bg_white'], fg=COLORS['text_secondary']).pack(side=tk.LEFT)
        self.dir_entry = tk.Entry(dir_row, textvariable=self.output_dir_var, state='readonly', font=FONTS['small'], bg=COLORS['input_bg'], fg=COLORS['text_primary'], relief=tk.FLAT, highlightthickness=1, highlightbackground=COLORS['border'])
        self.dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3)
        tk.Button(dir_row, text="...", command=self._select_output_dir, font=FONTS['small'], bg=COLORS['text_muted'], fg='white', relief=tk.FLAT, padx=8, pady=2).pack(side=tk.RIGHT, padx=(SPACING['xs'], 0))

        output_card = Card(main, "Opciones de Salida")
        formats_grid = tk.Frame(output_card.content, bg=COLORS['bg_white'])
        formats_grid.pack(fill=tk.X)
        StyledCheckbox(formats_grid, "PNG", self.save_png_var).grid(row=0, column=0, sticky='w')
        StyledCheckbox(formats_grid, "JPG", self.save_jpg_var).grid(row=0, column=1, sticky='w', padx=(SPACING['xl'], 0))
        StyledCheckbox(formats_grid, "GeoTIFF", self.save_tiff_var).grid(row=1, column=0, sticky='w')
        StyledCheckbox(formats_grid, "Leyenda", self.save_legend_var).grid(row=1, column=1, sticky='w', padx=(SPACING['xl'], 0))
        tk.Frame(output_card.content, bg=COLORS['border'], height=1).pack(fill=tk.X, pady=SPACING['md'])
        
        class_row = tk.Frame(output_card.content, bg=COLORS['bg_white'])
        class_row.pack(fill=tk.X)
        StyledCheckbox(class_row, "Clasificar elevaciones", self.classify_var).pack(side=tk.LEFT)
        tk.Label(class_row, text="Intervalo:", font=FONTS['body'], bg=COLORS['bg_white'], fg=COLORS['text_secondary']).pack(side=tk.LEFT, padx=(SPACING['lg'], SPACING['xs']))
        tk.Entry(class_row, textvariable=self.class_interval_var, width=6, font=FONTS['body'], bg=COLORS['input_bg'], fg=COLORS['text_primary'], relief=tk.FLAT, highlightthickness=1, highlightbackground=COLORS['border'], highlightcolor=COLORS['primary']).pack(side=tk.LEFT, ipady=2)
        tk.Label(class_row, text="m", font=FONTS['body'], bg=COLORS['bg_white'], fg=COLORS['text_secondary']).pack(side=tk.LEFT, padx=(SPACING['xs'], 0))

        btn_frame = tk.Frame(main, bg=COLORS['bg_light'])
        btn_frame.pack(fill=tk.X, pady=SPACING['lg'])
        self.process_button = ModernButton(btn_frame, text="PROCESAR", command=self._start_processing, bg_color=COLORS['success'], hover_color=COLORS['success_hover'], width=200, height=45)
        self.process_button.pack()
        self.process_button.configure(state=tk.DISABLED)
        
        self.progress_frame = tk.Frame(main, bg=COLORS['bg_light'])
        self.progress = ttk.Progressbar(self.progress_frame, mode='indeterminate', length=300)
        self.progress.pack()
        self.status_label = tk.Label(main, text="Seleccione un archivo para comenzar", font=FONTS['body'], bg=COLORS['bg_light'], fg=COLORS['text_muted'])
        self.status_label.pack(pady=(SPACING['sm'], 0))
        
        for var in [self.file_path, self.resolution_var, self.epsg_var, self.output_name_var, self.class_interval_var]:
            var.trace_add("write", self._validate_inputs)
            
    def _on_file_selected(self, filename):
        if filename:
            basename = os.path.splitext(os.path.basename(filename))[0]
            self.output_name_var.set(basename)
            self.output_dir_var.set(os.path.dirname(filename))
            
    def _select_output_dir(self):
        d = filedialog.askdirectory(initialdir=self.output_dir_var.get())
        if d: self.output_dir_var.set(d)

    def _update_colormap_preview(self, event=None):
        try:
            import numpy as np
            import matplotlib.pyplot as plt
            from PIL import Image, ImageTk
            cmap_name = self.colormap_var.get()
            cmap = plt.get_cmap(cmap_name)
            whitening = self.whitening_var.get() / 100.0
            gradient = np.linspace(0, 1, 100)
            gradient = np.vstack((gradient, gradient))
            img_array = cmap(gradient)
            rgb = img_array[:, :, :3]
            if whitening > 0: rgb = rgb * (1 - whitening) + whitening
            img_array = (rgb * 255).astype(np.uint8)
            img_pil = Image.fromarray(img_array).resize((150, 20), Image.NEAREST)
            self.preview_image = ImageTk.PhotoImage(img_pil)
            self.preview_label.config(image=self.preview_image)
        except: pass

    def _validate_inputs(self, *args):
        valid = True
        if not self.file_path.get(): valid = False
        try:
            float(self.resolution_var.get())
            if self.classify_var.get(): float(self.class_interval_var.get())
        except ValueError: valid = False
        self.process_button.configure(state=tk.NORMAL if valid else tk.DISABLED)
        self.status_label.config(text="✓ Listo para procesar" if valid else "Complete los campos requeridos", fg=COLORS['success'] if valid else COLORS['text_muted'])
        
    def _start_processing(self):
        if self.processing: return
        self.processing = True
        self.process_button.configure(state=tk.DISABLED)
        self.progress_frame.pack(fill=tk.X, pady=SPACING['sm'])
        self.progress['mode'] = 'determinate'
        self.progress['value'] = 0
        self.status_label.config(text="Procesando...", fg=COLORS['primary'])
        threading.Thread(target=self._run_processing, daemon=True).start()
        
    def _run_processing(self):
        try:
            xml_file = self.file_path.get()
            res = float(self.resolution_var.get())
            epsg = int(self.epsg_var.get())
            out_name = self.output_name_var.get()
            out_dir = self.output_dir_var.get() or os.path.dirname(xml_file)
            self._update_status("Leyendo LandXML...", 10)
            points, triangles = parse_landxml_surface(xml_file)
            self._update_status("Rasterizando TIN...", 30)
            grid_z, extent = rasterize_surface_tin(points, triangles, resolution=res)
            if self.save_tiff_var.get():
                self._update_status("Guardando GeoTIFF...", 60)
                save_geotiff(grid_z, extent, os.path.join(out_dir, out_name + ".tif"), epsg_code=epsg)
            if self.save_png_var.get() or self.save_jpg_var.get():
                self._update_status("Generando imágenes...", 80)
                class_interval = float(self.class_interval_var.get()) if self.classify_var.get() else None
                save_colored_map(grid_z, out_name, colormap=self.colormap_var.get(), output_dir=out_dir, class_interval=class_interval, whitening=self.whitening_var.get()/100.0, save_png=self.save_png_var.get(), save_jpg=self.save_jpg_var.get(), rotate_90=True)
                if self.save_png_var.get(): save_world_file(extent, grid_z.shape, os.path.join(out_dir, out_name + ".pgw"))
                if self.save_jpg_var.get(): save_world_file(extent, grid_z.shape, os.path.join(out_dir, out_name + ".jgw"))
            if self.save_legend_var.get():
                self._update_status("Generando leyenda...", 90)
                create_colormap_legend(grid_z, colormap=self.colormap_var.get(), output_path=os.path.join(out_dir, out_name + "_legend.png"), class_interval=float(self.class_interval_var.get()) if self.classify_var.get() else None, whitening=self.whitening_var.get()/100.0)
            self._update_status("Proceso completado exitosamente.", 100)
            self.root.after(0, self._on_complete, True, "Proceso completado exitosamente.")
        except Exception as e:
            self.root.after(0, self._on_complete, False, str(e))
            
    def _update_status(self, msg, percent=None):
        def _update():
            self.status_label.config(text=msg)
            if percent is not None: self.progress['value'] = percent
        self.root.after(0, _update)
        
    def _on_complete(self, success, msg):
        self.processing = False
        self.progress.stop()
        self.progress_frame.pack_forget()
        self.process_button.configure(state=tk.NORMAL)
        if success:
            self.status_label.config(text="✓ " + msg, fg=COLORS['success'])
            messagebox.showinfo("Éxito", msg)
        else:
            self.status_label.config(text="✗ Error", fg=COLORS['danger'])
            messagebox.showerror("Error", f"Ocurrió un error:\n{msg}")

class LandXMLDiffGUI:
    """
    Interfaz gráfica para comparar superficies LandXML.
    """
    def __init__(self, parent):
        from ..processing.diff import calculate_difference
        self.parent = parent
        self.root = parent
        self.is_standalone = isinstance(parent, (tk.Tk, tk.Toplevel))
        if self.is_standalone:
            self.parent.title("LandXML Diff")
            self.parent.geometry("540x780")
            self.parent.configure(bg=COLORS['bg_light'])
            center_window(self.parent)
        
        self.file1_path = tk.StringVar()
        self.file2_path = tk.StringVar()
        self.resolution_var = tk.StringVar(value="0.05")
        self.epsg_var = tk.StringVar(value="25830")
        self.output_name_var = tk.StringVar(value="landxml_diff")
        self.colormap_var = tk.StringVar(value="coolwarm_r")
        self.whitening_var = tk.IntVar(value=0)
        self.save_png_var = tk.BooleanVar(value=True)
        self.save_jpg_var = tk.BooleanVar(value=True)
        self.save_tiff_var = tk.BooleanVar(value=True)
        self.save_legend_var = tk.BooleanVar(value=True)
        self.classify_var = tk.BooleanVar(value=True)
        self.class_interval_var = tk.StringVar(value="1.00")
        self.output_dir_var = tk.StringVar(value="")
        self.processing = False
        
        self._create_ui()
    
    def _create_ui(self):
        main = tk.Frame(self.parent, bg=COLORS['bg_light'])
        main.pack(fill=tk.BOTH, expand=True, padx=SPACING['xl'], pady=SPACING['lg'])
        
        files_card = Card(main, "Archivos de Entrada")
        self.file1_selector = FileSelector(files_card.content, "Superficie Base (1)", self.file1_path)
        self.file1_selector.pack(fill=tk.X, pady=(0, SPACING['md']))
        self.file2_selector = FileSelector(files_card.content, "Superficie a Comparar (2)", self.file2_path, on_select=self._on_file2_selected)
        self.file2_selector.pack(fill=tk.X)
        
        config_card = Card(main, "Parámetros")
        params_grid = tk.Frame(config_card.content, bg=COLORS['bg_white'])
        params_grid.pack(fill=tk.X)
        ConfigRow(params_grid, "Resolución (m):", self.resolution_var, 8).grid(row=0, column=0, sticky='w', pady=SPACING['xs'])
        ConfigRow(params_grid, "Código EPSG:", self.epsg_var, 8).grid(row=0, column=1, sticky='w', pady=SPACING['xs'], padx=(SPACING['lg'], 0))
        ConfigRow(params_grid, "Nombre salida:", self.output_name_var, 16).grid(row=1, column=0, columnspan=2, sticky='w', pady=SPACING['xs'])
        
        colormap_row = tk.Frame(config_card.content, bg=COLORS['bg_white'])
        colormap_row.pack(fill=tk.X, pady=SPACING['xs'])
        tk.Label(colormap_row, text="Mapa de color:", font=FONTS['body'], width=16, anchor='w', bg=COLORS['bg_white'], fg=COLORS['text_secondary']).pack(side=tk.LEFT)
        self.colormap_combo = ttk.Combobox(colormap_row, textvariable=self.colormap_var, font=FONTS['body'], width=14, state='readonly')
        self.colormap_combo['values'] = ('coolwarm_r', 'coolwarm', 'RdBu_r', 'RdBu', 'seismic', 'bwr', 'RdYlGn_r', 'terrain', 'gist_earth', 'viridis', 'plasma', 'inferno', 'magma', 'cividis')
        self.colormap_combo.pack(side=tk.LEFT)
        self.preview_label = tk.Label(colormap_row, bg=COLORS['bg_white'], width=150, height=20)
        self.preview_label.pack(side=tk.LEFT, padx=(SPACING['sm'], 0))
        self.colormap_combo.bind("<<ComboboxSelected>>", self._update_colormap_preview)

        whiten_row = tk.Frame(config_card.content, bg=COLORS['bg_white'])
        whiten_row.pack(fill=tk.X, pady=(SPACING['xs'], 0))
        tk.Label(whiten_row, text="Blanqueamiento (%):", font=FONTS['body'], width=16, anchor='w', bg=COLORS['bg_white'], fg=COLORS['text_secondary']).pack(side=tk.LEFT)
        whiten_controls = tk.Frame(whiten_row, bg=COLORS['bg_white'])
        whiten_controls.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.whiten_scale = tk.Scale(whiten_controls, from_=0, to=100, orient=tk.HORIZONTAL, variable=self.whitening_var, length=250, bg=COLORS['bg_white'], highlightthickness=0, font=FONTS['small'], showvalue=0, command=lambda v: self._update_colormap_preview())
        self.whiten_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.whiten_spin = tk.Spinbox(whiten_controls, from_=0, to=100, textvariable=self.whitening_var, width=5, font=FONTS['body'], command=self._update_colormap_preview)
        self.whiten_spin.pack(side=tk.LEFT, padx=(SPACING['sm'], 0))
        self._update_colormap_preview()
        
        dir_row = tk.Frame(config_card.content, bg=COLORS['bg_white'])
        dir_row.pack(fill=tk.X, pady=(SPACING['sm'], 0))
        tk.Label(dir_row, text="Directorio salida:", font=FONTS['body'], width=16, anchor='w', bg=COLORS['bg_white'], fg=COLORS['text_secondary']).pack(side=tk.LEFT)
        self.dir_entry = tk.Entry(dir_row, textvariable=self.output_dir_var, state='readonly', font=FONTS['small'], bg=COLORS['input_bg'], fg=COLORS['text_primary'], relief=tk.FLAT, highlightthickness=1, highlightbackground=COLORS['border'])
        self.dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3)
        tk.Button(dir_row, text="...", command=self._select_output_dir, font=FONTS['small'], bg=COLORS['text_muted'], fg='white', relief=tk.FLAT, padx=8, pady=2).pack(side=tk.RIGHT, padx=(SPACING['xs'], 0))
        
        output_card = Card(main, "Opciones de Salida")
        formats_grid = tk.Frame(output_card.content, bg=COLORS['bg_white'])
        formats_grid.pack(fill=tk.X)
        StyledCheckbox(formats_grid, "PNG (transparencia)", self.save_png_var).grid(row=0, column=0, sticky='w')
        StyledCheckbox(formats_grid, "JPG", self.save_jpg_var).grid(row=0, column=1, sticky='w', padx=(SPACING['xl'], 0))
        StyledCheckbox(formats_grid, "GeoTIFF", self.save_tiff_var).grid(row=1, column=0, sticky='w')
        StyledCheckbox(formats_grid, "Leyenda", self.save_legend_var).grid(row=1, column=1, sticky='w', padx=(SPACING['xl'], 0))
        tk.Frame(output_card.content, bg=COLORS['border'], height=1).pack(fill=tk.X, pady=SPACING['md'])
        
        class_row = tk.Frame(output_card.content, bg=COLORS['bg_white'])
        class_row.pack(fill=tk.X)
        StyledCheckbox(class_row, "Clasificar elevaciones", self.classify_var).pack(side=tk.LEFT)
        tk.Label(class_row, text="Intervalo:", font=FONTS['body'], bg=COLORS['bg_white'], fg=COLORS['text_secondary']).pack(side=tk.LEFT, padx=(SPACING['lg'], SPACING['xs']))
        tk.Entry(class_row, textvariable=self.class_interval_var, width=6, font=FONTS['body'], bg=COLORS['input_bg'], fg=COLORS['text_primary'], relief=tk.FLAT, highlightthickness=1, highlightbackground=COLORS['border'], highlightcolor=COLORS['primary']).pack(side=tk.LEFT, ipady=2)
        tk.Label(class_row, text="m", font=FONTS['body'], bg=COLORS['bg_white'], fg=COLORS['text_secondary']).pack(side=tk.LEFT, padx=(SPACING['xs'], 0))
        
        btn_frame = tk.Frame(main, bg=COLORS['bg_light'])
        btn_frame.pack(fill=tk.X, pady=SPACING['lg'])
        self.process_btn = ModernButton(btn_frame, text="PROCESAR", command=self._start_processing, bg_color=COLORS['success'], hover_color=COLORS['success_hover'], width=200, height=45)
        self.process_btn.pack()
        self.process_btn.configure(state=tk.DISABLED)
        
        self.progress_frame = tk.Frame(main, bg=COLORS['bg_light'])
        self.progress_bar = ttk.Progressbar(self.progress_frame, mode='indeterminate', length=300)
        self.progress_bar.pack()
        self.status_label = tk.Label(main, text="Seleccione los archivos para comenzar", font=FONTS['body'], bg=COLORS['bg_light'], fg=COLORS['text_muted'])
        self.status_label.pack(pady=(SPACING['sm'], 0))
        
        self.file1_path.trace_add('write', self._check_ready)
        self.file2_path.trace_add('write', self._check_ready)
    
    def _update_colormap_preview(self, event=None):
        try:
            import numpy as np
            import matplotlib.pyplot as plt
            from PIL import Image, ImageTk
            cmap_name = self.colormap_var.get()
            cmap = plt.get_cmap(cmap_name)
            whitening = self.whitening_var.get() / 100.0
            gradient = np.linspace(0, 1, 100)
            gradient = np.vstack((gradient, gradient))
            img_array = cmap(gradient)
            rgb = img_array[:, :, :3]
            if whitening > 0: rgb = rgb * (1 - whitening) + whitening
            img_array = (rgb * 255).astype(np.uint8)
            img_pil = Image.fromarray(img_array).resize((150, 20), Image.NEAREST)
            self.preview_image = ImageTk.PhotoImage(img_pil)
            self.preview_label.config(image=self.preview_image, width=150, height=20)
        except Exception as e: print(f"Error generando preview: {e}")

    def _on_file2_selected(self, filename): self.output_dir_var.set(os.path.dirname(filename))
    def _select_output_dir(self):
        directory = filedialog.askdirectory(title="Seleccionar Directorio de Salida")
        if directory: self.output_dir_var.set(directory)
    def _check_ready(self, *args):
        ready = self.file1_path.get() and self.file2_path.get()
        self.process_btn.configure(state=tk.NORMAL if ready else tk.DISABLED)
        self.status_label.config(text="✓ Listo para procesar" if ready else "Seleccione los archivos para comenzar", fg=COLORS['success'] if ready else COLORS['text_muted'])
    def _update_progress(self, message, percent=None):
        self.status_label.config(text=message, fg=COLORS['primary'])
        if percent is not None: self.progress_bar['value'] = percent
        self.root.update_idletasks()
    def _start_processing(self):
        try:
            if float(self.resolution_var.get()) <= 0: raise ValueError()
            if int(self.epsg_var.get()) <= 0: raise ValueError()
            if not self.output_name_var.get().strip(): raise ValueError()
            if self.classify_var.get() and float(self.class_interval_var.get()) <= 0: raise ValueError()
        except: messagebox.showerror("Error", "Parámetros inválidos"); return
        self.processing = True
        self.process_btn.configure(state=tk.DISABLED)
        self.progress_frame.pack(fill=tk.X, pady=SPACING['sm'])
        self.progress_bar['mode'] = 'determinate'
        self.progress_bar['value'] = 0
        threading.Thread(target=self._run_processing, daemon=True).start()
    def _run_processing(self):
        try:
            from .apps import LandXMLDiffGUI
            # Evitar importación circular si se moviera a otro lugar, pero aquí usamos apps/landxml_diff.py lógica
            # En realidad, usaremos una versión local de la lógica o importaremos apps.landxml_diff si está en el path
            # Pero para ser limpios, la lógica de landxml_diff debería estar en processing.diff
            from apps.landxml_diff import main as process_landxml_diff
            success, message = process_landxml_diff(surface_file1=self.file1_path.get(), surface_file2=self.file2_path.get(), output_name=self.output_name_var.get().strip(), resolution=float(self.resolution_var.get()), epsg_code=int(self.epsg_var.get()), colormap=self.colormap_var.get(), save_jpg=self.save_jpg_var.get(), save_png=self.save_png_var.get(), save_tiff=self.save_tiff_var.get(), save_legend=self.save_legend_var.get(), output_dir=self.output_dir_var.get().strip() or None, class_interval=float(self.class_interval_var.get()) if self.classify_var.get() else None, whitening=self.whitening_var.get()/100.0, progress_callback=self._update_progress)
            self.root.after(0, self._on_complete, success, message)
        except Exception as e: self.root.after(0, self._on_complete, False, str(e))
    def _on_complete(self, success, message):
        self.processing = False
        self.progress_bar.stop()
        self.progress_frame.pack_forget()
        self.process_btn.configure(state=tk.NORMAL)
        if success:
            self.status_label.config(text="✓ " + message, fg=COLORS['success'])
            messagebox.showinfo("Completado", f"{message}\n\nArchivos guardados en:\n{self.output_dir_var.get() or '../output'}")
        else:
            self.status_label.config(text="✗ " + message, fg=COLORS['danger'])
            messagebox.showerror("Error", message)
