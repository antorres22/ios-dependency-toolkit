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

def add_statistics(root, y_position, x_position, spm_modules, unique_dependencies, version_checker, parent):
    """Añade estadísticas del proyecto con información detallada de dependencias"""
    stats_id = f'statistics_{uuid.uuid4().hex[:8]}'
    total_modules = sum(len(pkg['modules']) for pkg in spm_modules)
    
    # Contenedor principal de estadísticas
    stats = ET.SubElement(root, 'mxCell')
    stats.set('id', stats_id)
    stats.set('value', 'Estadísticas')
    stats.set('style', 'swimlane;fontStyle=1;childLayout=stackLayout;horizontal=1;startSize=30;fillColor=#f5f5f5;horizontalStack=0;resizeParent=1;resizeParentMax=0;resizeLast=0;collapsible=1;marginBottom=0;strokeColor=#666666;fontSize=12;')
    stats.set('vertex', '1')
    stats.set('parent', parent)
    
    # Ajustar dimensiones
    width = 380
    height = 120 + (len(unique_dependencies) * 100)
    
    geo = ET.SubElement(stats, 'mxGeometry')
    geo.set('x', str(x_position))
    geo.set('y', str(y_position))
    geo.set('width', str(width))
    geo.set('height', str(height))
    geo.set('as', 'geometry')
    
    # Información general
    general_info = ET.SubElement(root, 'mxCell')
    general_info.set('id', f'general_info_{stats_id}')
    general_info.set('value', 
        '<p style="margin:0px;">' +
        f'Total de Módulos: {total_modules}</p><p style="margin:0px;">' + 
        f'Total de Dependencias Externas: {len(unique_dependencies)}</p><p style="margin:0px;">' +
        f'Total de Ficheros: {len(spm_modules)}</p>')
    general_info.set('style', 'text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;spacingLeft=4;spacingRight=4;overflow=hidden;rotatable=0;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;fontSize=11;whiteSpace=wrap;')
    general_info.set('vertex', '1')
    general_info.set('parent', stats_id)
    
    gen_geo = ET.SubElement(general_info, 'mxGeometry')
    gen_geo.set('y', '30')  # Empieza después del título
    gen_geo.set('width', str(width))
    gen_geo.set('height', '60')
    gen_geo.set('as', 'geometry')
    
    # Título de dependencias
    deps_title = ET.SubElement(root, 'mxCell')
    deps_title.set('id', f'deps_title_{stats_id}')
    deps_title.set('value', 'Dependencias Externas')
    deps_title.set('style', 'text;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;spacingLeft=4;spacingRight=4;overflow=hidden;rotatable=0;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;fontSize=12;fontStyle=1')
    deps_title.set('vertex', '1')
    deps_title.set('parent', stats_id)
    
    deps_title_geo = ET.SubElement(deps_title, 'mxGeometry')
    deps_title_geo.set('y', '90')
    deps_title_geo.set('width', str(width))
    deps_title_geo.set('height', '30')
    deps_title_geo.set('as', 'geometry')
    
    # Agregar cada dependencia
    y_offset = 120
    for i, dep in enumerate(sorted(unique_dependencies.values(), key=lambda x: x['name'].lower())):
        # Separador
        if i > 0:
            separator = ET.SubElement(root, 'mxCell')
            separator.set('id', f'separator_{stats_id}_{i}')
            separator.set('value', '')
            separator.set('style', 'line;strokeWidth=1;fillColor=none;align=left;verticalAlign=middle;spacingTop=-1;spacingLeft=3;spacingRight=3;rotatable=0;labelPosition=right;points=[];portConstraint=eastwest;strokeColor=#CCCCCC;')
            separator.set('vertex', '1')
            separator.set('parent', stats_id)
            
            sep_geo = ET.SubElement(separator, 'mxGeometry')
            sep_geo.set('y', str(y_offset))
            sep_geo.set('width', str(width))
            sep_geo.set('height', '8')
            sep_geo.set('as', 'geometry')
            
            y_offset += 8
        
        # Información de la dependencia
        latest_version = version_checker.get_latest_version(dep['url'])
        status = version_checker._get_version_status(dep['version'], latest_version, dep['url'])
        
        dep_cell = ET.SubElement(root, 'mxCell')
        dep_cell.set('id', f'dep_info_{stats_id}_{i}')
        dep_cell.set('value',
            '<p style="margin:0px;font-weight:bold;">' +
            f'{dep["name"]}</p>' +
            f'<p style="margin:0px;">URL: {dep["url"]}</p>' +
            f'<p style="margin:0px;">Versión actual: {dep["version"]}</p>' +
            f'<p style="margin:0px;">Última versión disponible: {latest_version}</p>' +
            f'<p style="margin:0px;">Status: {status}</p>')
        dep_cell.set('style', 'text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;spacingLeft=4;spacingRight=4;overflow=hidden;rotatable=0;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;fontSize=11;whiteSpace=wrap;')
        dep_cell.set('vertex', '1')
        dep_cell.set('parent', stats_id)
        
        dep_geo = ET.SubElement(dep_cell, 'mxGeometry')
        dep_geo.set('y', str(y_offset))
        dep_geo.set('width', str(width))
        dep_geo.set('height', '80')
        dep_geo.set('as', 'geometry')
        
        y_offset += 90

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