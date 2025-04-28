import xml.etree.ElementTree as ET
import uuid

def add_version_legend(root, y_position, x_position, parent):
    """Añade la leyenda de los iconos de versiones usando Entity Relation List"""
    legend_id = f'version_legend_{uuid.uuid4().hex[:8]}'
    
    # Contenedor de la leyenda
    legend = ET.SubElement(root, 'mxCell')
    legend.set('id', legend_id)
    legend.set('value', 'Estados de Versiones')
    legend.set('style', 'swimlane;fontStyle=1;childLayout=stackLayout;horizontal=1;startSize=30;fillColor=#f5f5f5;horizontalStack=0;resizeParent=1;resizeParentMax=0;resizeLast=0;collapsible=0;marginBottom=0;strokeColor=#666666;fontSize=12;')
    legend.set('vertex', '1')
    legend.set('parent', parent)
    
    geo = ET.SubElement(legend, 'mxGeometry')
    geo.set('x', str(x_position))
    geo.set('y', str(y_position))
    geo.set('width', '250')
    geo.set('height', '150')
    geo.set('as', 'geometry')
    
    # Estados con mejor espaciado
    states = [
        ('🔴 Diferencia Major', 'Indica una diferencia en versión mayor'),
        ('🟡 Diferencia Minor o Patch > 5', 'Indica diferencia en versión menor o parche mayor a 5'),
        ('🟢 Versión actualizada', 'Versión actual o diferencia en parche menor a 5'),
        ('⚫ No determinado', 'No se pudo determinar la versión')
    ]
    
    for i, (state, desc) in enumerate(states):
        state_cell = ET.SubElement(root, 'mxCell')
        state_cell.set('id', f'legend_state_{legend_id}_{i}')
        state_cell.set('value', f'{state}')
        state_cell.set('style', 'text;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;spacingLeft=4;spacingRight=4;overflow=hidden;rotatable=0;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;fontSize=11;')
        state_cell.set('vertex', '1')
        state_cell.set('parent', legend_id)
        
        state_geo = ET.SubElement(state_cell, 'mxGeometry')
        state_geo.set('y', str(30 + (i * 30)))  # Mayor espaciado entre elementos
        state_geo.set('width', '250')
        state_geo.set('height', '30')
        state_geo.set('as', 'geometry')

def add_statistics(root, y_position, x_position, spm_modules, unique_dependencies, version_checker, parent, pod_dependencies=None):
    """Añade estadísticas del proyecto con información detallada de dependencias"""
    stats_id = _create_statistics_container(root, x_position, y_position, parent)
    y_offset = _add_general_info(root, stats_id, spm_modules, unique_dependencies, pod_dependencies)
    
    # Sección SPM
    if unique_dependencies:
        y_offset = add_spm_dependencies_section(root, stats_id, y_offset, unique_dependencies, version_checker)
    
    # Sección Pods
    if pod_dependencies:
        y_offset = add_pods_dependencies_section(root, stats_id, y_offset, pod_dependencies, version_checker)

def _create_statistics_container(root, x_position, y_position, parent):
    """Crea el contenedor principal de estadísticas"""
    stats_id = f'statistics_{uuid.uuid4().hex[:8]}'
    
    stats = ET.SubElement(root, 'mxCell')
    stats.set('id', stats_id)
    stats.set('value', 'Estadísticas')
    stats.set('style', 'swimlane;fontStyle=1;childLayout=stackLayout;horizontal=1;startSize=30;fillColor=#f5f5f5;horizontalStack=0;resizeParent=1;resizeParentMax=0;resizeLast=0;collapsible=1;marginBottom=0;strokeColor=#666666;fontSize=12;')
    stats.set('vertex', '1')
    stats.set('parent', parent)
    
    width = 380
    geo = ET.SubElement(stats, 'mxGeometry')
    geo.set('x', str(x_position))
    geo.set('y', str(y_position))
    geo.set('width', str(width))
    geo.set('height', '2000')  # Altura dinámica
    geo.set('as', 'geometry')
    
    return stats_id
def _add_general_info(root, stats_id, spm_modules, unique_dependencies, pod_dependencies):
    """Añade la información general de estadísticas"""
    total_spm_modules = sum(len(pkg['modules']) for pkg in spm_modules)
    total_pods = len(pod_dependencies) if pod_dependencies else 0
    width = 380
    
    general_info = ET.SubElement(root, 'mxCell')
    general_info.set('id', f'general_info_{stats_id}')
    general_info.set('value', 
        '<p style="margin:0px;">' +
        f'Total de Módulos SPM: {total_spm_modules}</p>' +
        f'<p style="margin:0px;">Total de Pods: {total_pods}</p>' +
        f'<p style="margin:0px;">Total de Dependencias SPM Externas: {len(unique_dependencies)}</p>' +
        f'<p style="margin:0px;">Total de Ficheros: {len(spm_modules)}</p>')
    general_info.set('style', 'text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;spacingLeft=4;spacingRight=4;overflow=hidden;rotatable=0;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;fontSize=11;whiteSpace=wrap;')
    general_info.set('vertex', '1')
    general_info.set('parent', stats_id)
    
    gen_geo = ET.SubElement(general_info, 'mxGeometry')
    gen_geo.set('y', '30')
    gen_geo.set('width', str(width))
    gen_geo.set('height', '80')
    gen_geo.set('as', 'geometry')
    
    return 110  # Retorna el siguiente y_offset

def _add_section_title(root, stats_id, title, y_offset, width):
    """Añade un título de sección"""
    title_cell = ET.SubElement(root, 'mxCell')
    title_cell.set('id', f'title_{stats_id}_{uuid.uuid4().hex[:8]}')
    title_cell.set('value', title)
    title_cell.set('style', 'text;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;spacingLeft=4;spacingRight=4;overflow=hidden;rotatable=0;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;fontSize=12;fontStyle=1')
    title_cell.set('vertex', '1')
    title_cell.set('parent', stats_id)
    
    title_geo = ET.SubElement(title_cell, 'mxGeometry')
    title_geo.set('y', str(y_offset))
    title_geo.set('width', str(width))
    title_geo.set('height', '30')
    title_geo.set('as', 'geometry')
    
    return y_offset + 30

def _add_separator(root, stats_id, y_offset, width, is_section=False):
    """Añade un separador entre elementos"""
    separator = ET.SubElement(root, 'mxCell')
    separator.set('id', f'separator_{stats_id}_{uuid.uuid4().hex[:8]}')
    separator.set('value', '')
    
    # Estilo diferente para separadores de sección
    if is_section:
        style = 'line;strokeWidth=2;fillColor=none;align=left;verticalAlign=middle;spacingTop=-1;spacingLeft=3;spacingRight=3;rotatable=0;labelPosition=right;points=[];portConstraint=eastwest;strokeColor=#666666;'
        height = '20'
        y_offset_increment = 30
    else:
        style = 'line;strokeWidth=1;fillColor=none;align=left;verticalAlign=middle;spacingTop=-1;spacingLeft=3;spacingRight=3;rotatable=0;labelPosition=right;points=[];portConstraint=eastwest;strokeColor=#CCCCCC;'
        height = '8'
        y_offset_increment = 8
    
    separator.set('style', style)
    separator.set('vertex', '1')
    separator.set('parent', stats_id)
    
    sep_geo = ET.SubElement(separator, 'mxGeometry')
    sep_geo.set('y', str(y_offset))
    sep_geo.set('width', str(width))
    sep_geo.set('height', height)
    sep_geo.set('as', 'geometry')
    
    return y_offset + y_offset_increment

def add_spm_dependencies_section(root, stats_id, y_offset, unique_dependencies, version_checker):
    """Añade la sección de dependencias SPM"""
    width = 380
    
    # Listar dependencias SPM
    for i, dep in enumerate(sorted(unique_dependencies.values(), key=lambda x: x['name'].lower())):
        if i > 0:
            y_offset = _add_separator(root, stats_id, y_offset, width)
        
        y_offset = add_spm_dependency_info(root, stats_id, dep, version_checker, y_offset, width)
    
    return y_offset

def add_spm_dependency_info(root, stats_id, dep, version_checker, y_offset, width):
    """Añade la información de una dependencia SPM específica"""
    latest_version = version_checker.get_latest_version(dep['url'])
    status = version_checker._get_version_status(dep['version'], latest_version, dep['url'])
    
    dep_cell = ET.SubElement(root, 'mxCell')
    dep_cell.set('id', f'dep_info_spm_{stats_id}_{uuid.uuid4().hex[:8]}')
    
    # Crear el contenido HTML con información adicional si es una dependencia directa
    dep_type = dep.get('type', 'spm_module')
    source_info = ""
    if dep_type == 'spm_app_direct' and 'source' in dep:
        source_info = f'<p style="margin:0px;">Fuente: {dep["source"]}</p>'
    
    dep_cell.set('value',
        '<p style="margin:0px;font-weight:bold;">' +
        f'{dep["name"]}</p>' +
        f'<p style="margin:0px;">URL: {dep["url"]}</p>' +
        f'<p style="margin:0px;">Versión actual: {dep["version"]}</p>' +
        f'<p style="margin:0px;">Última versión disponible: {latest_version}</p>' +
        f'{source_info}' +
        f'<p style="margin:0px;">Status: {status}</p>')
    
    # Estilo diferente si es una dependencia directa de la app
    if dep_type == 'spm_app_direct':
        dep_cell.set('style', 'text;html=1;strokeColor=none;fillColor=#e6f2ff;align=left;verticalAlign=middle;spacingLeft=4;spacingRight=4;overflow=hidden;rotatable=0;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;fontSize=11;whiteSpace=wrap;')
    else:
        dep_cell.set('style', 'text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;spacingLeft=4;spacingRight=4;overflow=hidden;rotatable=0;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;fontSize=11;whiteSpace=wrap;')
    
    dep_cell.set('vertex', '1')
    dep_cell.set('parent', stats_id)
    
    # Ajustar altura según el contenido
    cell_height = 80
    if source_info:
        cell_height = 100  # Más alto para acomodar la información adicional
    
    dep_geo = ET.SubElement(dep_cell, 'mxGeometry')
    dep_geo.set('y', str(y_offset))
    dep_geo.set('width', str(width))
    dep_geo.set('height', str(cell_height))
    dep_geo.set('as', 'geometry')
    
    return y_offset + cell_height + 10  # Añadir un pequeño espacio adicional

def add_pods_dependencies_section(root, stats_id, y_offset, pod_dependencies, version_checker):
    """Añade la sección de dependencias de CocoaPods"""
    width = 380
    
    # Agregar separador de sección
    y_offset = _add_separator(root, stats_id, y_offset, width, is_section=True)
    
    # Agregar título de sección
    y_offset = _add_section_title(root, stats_id, 'Dependencias CocoaPods', y_offset, width)
    
    # Listar dependencias Pods
    for i, pod in enumerate(sorted(pod_dependencies, key=lambda x: x['name'].lower())):
        if i > 0:
            y_offset = _add_separator(root, stats_id, y_offset, width)
        
        y_offset = _add_pod_dependency_info(root, stats_id, pod, version_checker, y_offset, width)
    
    return y_offset

def _add_pod_dependency_info(root, stats_id, pod, version_checker, y_offset, width):
   """Añade la información de una dependencia Pod específica"""
   pod_cell = ET.SubElement(root, 'mxCell')
   pod_cell.set('id', f'dep_info_pod_{stats_id}_{uuid.uuid4().hex[:8]}')
   
   # Determinar estado comparando versiones
   status = "⚫"
   if pod.get('version', 'N/A') != 'N/A' and pod.get('latest_version', 'N/A') != 'N/A':
       current_version = pod['version']
       latest_version = pod['latest_version']
       try:
           if current_version == latest_version:
               status = "🟢"
           elif current_version < latest_version:
               status = "🔴"
           else:
               status = "🟡"
       except:
           status = "⚫"
   
   pod_info = f'<p style="margin:0px;font-weight:bold;">{pod["name"]}</p>'
   pod_info += f'<p style="margin:0px;">Versión actual: {pod.get("version", "N/A")}</p>'
   pod_info += f'<p style="margin:0px;">Última versión disponible: {pod.get("latest_version", "N/A")}</p>'
   pod_info += f'<p style="margin:0px;">Status: {status}</p>'
   
   if pod.get('url'):
       pod_info += f'<p style="margin:0px;">Git: {pod["url"]}</p>'
   
   pod_cell.set('value', pod_info)
   pod_cell.set('style', 'text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;spacingLeft=4;spacingRight=4;overflow=hidden;rotatable=0;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;fontSize=11;whiteSpace=wrap;')
   pod_cell.set('vertex', '1')
   pod_cell.set('parent', stats_id)
   
   pod_geo = ET.SubElement(pod_cell, 'mxGeometry')
   pod_geo.set('y', str(y_offset))
   pod_geo.set('width', str(width))
   pod_geo.set('height', '80')
   pod_geo.set('as', 'geometry')
   
   return y_offset + 90

def add_conflicts_section(root, y_position, x_position, conflicts, parent):
    """Añade la sección de conflictos al diagrama"""
    conflicts_id = f'conflicts_{uuid.uuid4().hex[:8]}'
    
    conflicts_cell = ET.SubElement(root, 'mxCell')
    conflicts_cell.set('id', conflicts_id)
    conflicts_cell.set('value', '⚠️ Conflictos Detectados')
    conflicts_cell.set('style', 'swimlane;fontStyle=1;childLayout=stackLayout;horizontal=1;startSize=30;fillColor=#ffe6cc;horizontalStack=0;resizeParent=1;resizeParentMax=0;resizeLast=0;collapsible=1;marginBottom=0;strokeColor=#d79b00;fontSize=12;')
    conflicts_cell.set('vertex', '1')
    conflicts_cell.set('parent', parent)
    
    height = 50 + (len(conflicts) * 40)
    width = 380
    
    geo = ET.SubElement(conflicts_cell, 'mxGeometry')
    geo.set('x', str(x_position))
    geo.set('y', str(y_position))
    geo.set('width', str(width))
    geo.set('height', str(height))
    geo.set('as', 'geometry')
    
    y_offset = 30
    for i, conflict in enumerate(conflicts):
        conflict_item = ET.SubElement(root, 'mxCell')
        conflict_item.set('id', f'conflict_{conflicts_id}_{i}')
        
        conflict_text = f'<p style="margin:0px;font-weight:bold;">{conflict["package"]}:</p>'
        for version_info in conflict['versions']:
            conflict_text += f'<p style="margin:0px;">• {version_info["module"]}: {version_info["version"]}</p>'
        
        conflict_item.set('value', conflict_text)
        conflict_item.set('style', 'text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;spacingLeft=4;spacingRight=4;overflow=hidden;rotatable=0;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;fontSize=11;whiteSpace=wrap;')
        conflict_item.set('vertex', '1')
        conflict_item.set('parent', conflicts_id)
        
        item_geo = ET.SubElement(conflict_item, 'mxGeometry')
        item_geo.set('y', str(y_offset))
        item_geo.set('width', str(width - 20))
        item_geo.set('height', '40')
        item_geo.set('as', 'geometry')
        
        y_offset += 40