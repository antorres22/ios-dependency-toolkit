# spm_generator/diagram/components.py

import xml.etree.ElementTree as ET
import uuid

def add_version_legend(root, y_position, x_position):
    """Añade la leyenda de los iconos de versiones usando Entity Relation List"""
    legend_id = f'version_legend_{uuid.uuid4().hex[:8]}'
    
    legend = ET.SubElement(root, 'mxCell')
    legend.set('id', legend_id)
    legend.set('value', 'Estados de Versiones')
    legend.set('style', 'shape=mxgraph.er.list;align=left;verticalAlign=top;horizontal=1;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;fontSize=14;fontStyle=1')
    legend.set('vertex', '1')
    legend.set('parent', '1')
    
    geo = ET.SubElement(legend, 'mxGeometry')
    geo.set('x', str(x_position))
    geo.set('y', str(y_position))
    geo.set('width', '250')
    geo.set('height', '150')
    geo.set('as', 'geometry')
    
    states = [
        ('🔴 Diferencia Major', 'Indica una diferencia en versión mayor'),
        ('🟡 Diferencia Minor o Patch > 5', 'Indica diferencia en versión menor o parche mayor a 5'),
        ('🟢 Versión actualizada', 'Versión actual o diferencia en parche menor a 5'),
        ('⚫ No determinado', 'No se pudo determinar la versión')
    ]
    
    y_offset = 30
    
    for i, (state, desc) in enumerate(states):
        state_cell = ET.SubElement(root, 'mxCell')
        state_cell.set('id', f'legend_state_{legend_id}_{i}')
        state_cell.set('value', f'{state}')
        state_cell.set('style', 'text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=top;whiteSpace=wrap;rounded=0;fontSize=11;')
        state_cell.set('vertex', '1')
        state_cell.set('parent', legend_id)
        
        state_geo = ET.SubElement(state_cell, 'mxGeometry')
        state_geo.set('x', '10')
        state_geo.set('y', str(y_offset))
        state_geo.set('width', '230')
        state_geo.set('height', '20')
        state_geo.set('as', 'geometry')
        state_geo.set('relative', '0')
        
        y_offset += 25

def add_statistics(root, y_position, x_position, spm_modules, unique_dependencies, version_checker):
    """Añade estadísticas del proyecto con información detallada de dependencias"""
    stats_id = f'statistics_{uuid.uuid4().hex[:8]}'
    
    total_modules = sum(len(pkg['modules']) for pkg in spm_modules)
    
    # Crear el contenedor con estilo Entity Relation List
    stats = ET.SubElement(root, 'mxCell')
    stats.set('id', stats_id)
    stats.set('value', 'Estadísticas')
    stats.set('style', 'shape=mxgraph.er.list;align=left;verticalAlign=top;horizontal=1;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;fontSize=14;fontStyle=1')
    stats.set('vertex', '1')
    stats.set('parent', '1')
    
    # Ajustar dimensiones
    base_width = 300
    base_height = 120 + (len(unique_dependencies) * 100)
    width = int(base_width * 1.3)
    height = int(base_height * 1.3)
    
    geo = ET.SubElement(stats, 'mxGeometry')
    geo.set('x', str(x_position))
    geo.set('y', str(y_position))
    geo.set('width', str(width))
    geo.set('height', str(height))
    geo.set('as', 'geometry')
    
    # Agregar información general
    y_offset = 30
    general_info = ET.SubElement(root, 'mxCell')
    general_info.set('id', f'general_info_{stats_id}')
    general_info.set('value', 
        f'Total de Módulos: {total_modules}<br>' + 
        f'Total de Dependencias Externas: {len(unique_dependencies)}<br>' +
        f'Total de Ficheros: {len(spm_modules)}')
    general_info.set('style', 'text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=top;whiteSpace=wrap;rounded=0;fontSize=12;')
    general_info.set('vertex', '1')
    general_info.set('parent', stats_id)
    
    gen_geo = ET.SubElement(general_info, 'mxGeometry')
    gen_geo.set('x', '10')
    gen_geo.set('y', str(y_offset))
    gen_geo.set('width', str(width - 20))
    gen_geo.set('height', '60')
    gen_geo.set('as', 'geometry')
    gen_geo.set('relative', '0')
    
    y_offset += 80
    
    # Agregar título de dependencias
    deps_title = ET.SubElement(root, 'mxCell')
    deps_title.set('id', f'deps_title_{stats_id}')
    deps_title.set('value', 'Dependencias Externas')
    deps_title.set('style', 'text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=top;whiteSpace=wrap;rounded=0;fontSize=12;fontStyle=1')
    deps_title.set('vertex', '1')
    deps_title.set('parent', stats_id)
    
    title_geo = ET.SubElement(deps_title, 'mxGeometry')
    title_geo.set('x', '10')
    title_geo.set('y', str(y_offset))
    title_geo.set('width', str(width - 20))
    title_geo.set('height', '20')
    title_geo.set('as', 'geometry')
    title_geo.set('relative', '0')
    
    y_offset += 30
    
    # Agregar dependencias
    for i, dep in enumerate(sorted(unique_dependencies.values(), key=lambda x: x['name'].lower())):
        # Agregar separador
        if i > 0:
            separator = ET.SubElement(root, 'mxCell')
            separator.set('id', f'separator_{stats_id}_{i}')
            separator.set('value', '')
            separator.set('style', 'line;strokeWidth=1;fillColor=none;align=left;verticalAlign=middle;spacingTop=-1;spacingLeft=3;spacingRight=3;rotatable=0;labelPosition=right;points=[];portConstraint=eastwest;strokeColor=#CCCCCC;')
            separator.set('vertex', '1')
            separator.set('parent', stats_id)
            
            sep_geo = ET.SubElement(separator, 'mxGeometry')
            sep_geo.set('x', '10')
            sep_geo.set('y', str(y_offset))
            sep_geo.set('width', str(width - 20))
            sep_geo.set('height', '8')
            sep_geo.set('as', 'geometry')
            sep_geo.set('relative', '0')
            
            y_offset += 8
        
        # Agregar información de la dependencia
        latest_version = version_checker.get_latest_version(dep['url'])
        status = version_checker._get_version_status(dep['version'], latest_version, dep['url'])
        
        dep_cell = ET.SubElement(root, 'mxCell')
        dep_cell.set('id', f'dep_info_{stats_id}_{i}')
        dep_cell.set('value',
            f'<b>{dep["name"]}</b><br>' +
            f'URL: {dep["url"]}<br>' +
            f'Versión actual: {dep["version"]}<br>' +
            f'Última versión disponible: {latest_version}<br>' +
            f'Status: {status}')
        dep_cell.set('style', 'text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=top;whiteSpace=wrap;rounded=0;fontSize=11;')
        dep_cell.set('vertex', '1')
        dep_cell.set('parent', stats_id)
        
        dep_geo = ET.SubElement(dep_cell, 'mxGeometry')
        dep_geo.set('x', '10')
        dep_geo.set('y', str(y_offset))
        dep_geo.set('width', str(width - 20))
        dep_geo.set('height', '80')
        dep_geo.set('as', 'geometry')
        dep_geo.set('relative', '0')
        
        y_offset += 90

def add_conflicts_section(root, y_position, x_position, conflicts):
    """Añade la sección de conflictos al diagrama"""
    conflicts_id = f'conflicts_{uuid.uuid4().hex[:8]}'
    
    conflicts_cell = ET.SubElement(root, 'mxCell')
    conflicts_cell.set('id', conflicts_id)
    conflicts_cell.set('value', '⚠️ Conflictos Detectados')
    conflicts_cell.set('style', 'shape=mxgraph.er.list;align=left;verticalAlign=top;horizontal=1;whiteSpace=wrap;html=1;fillColor=#ffe6cc;strokeColor=#d79b00;fontSize=14;fontStyle=1')
    conflicts_cell.set('vertex', '1')
    conflicts_cell.set('parent', '1')
    
    height = 50 + (len(conflicts) * 40)
    
    geo = ET.SubElement(conflicts_cell, 'mxGeometry')
    geo.set('x', str(x_position))
    geo.set('y', str(y_position))
    geo.set('width', '300')
    geo.set('height', str(height))
    geo.set('as', 'geometry')
    
    y_offset = 30
    for i, conflict in enumerate(conflicts):
        conflict_item = ET.SubElement(root, 'mxCell')
        conflict_item.set('id', f'conflict_{conflicts_id}_{i}')
        
        conflict_text = f'<b>{conflict["package"]}</b>:<br>'
        for version_info in conflict['versions']:
            conflict_text += f'• {version_info["module"]}: {version_info["version"]}<br>'
        
        conflict_item.set('value', conflict_text)
        conflict_item.set('style', 'text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=top;whiteSpace=wrap;rounded=0;fontSize=11;')
        conflict_item.set('vertex', '1')
        conflict_item.set('parent', conflicts_id)
        
        item_geo = ET.SubElement(conflict_item, 'mxGeometry')
        item_geo.set('x', '10')
        item_geo.set('y', str(y_offset))
        item_geo.set('width', '280')
        item_geo.set('height', '40')
        item_geo.set('as', 'geometry')
        item_geo.set('relative', '0')
        
        y_offset += 40

def add_dependency_connections(root, module_cells, spm_modules):
    """
    Agrega conexiones de dependencia entre módulos.
    La flecha sale del lado izquierdo del módulo que declara la dependencia
    y apunta al lado derecho del módulo del que depende, en línea recta.
    """
    for pkg_idx, package_group in enumerate(spm_modules):
        for i, module in enumerate(package_group['modules']):
            source_id = f'module_{pkg_idx}_{i}'
            
            for dep in module['dependencies']:
                if dep.get('isLocal', False) and dep['name'] in module_cells:
                    target_id = module_cells[dep['name']]
                    
                    edge = ET.SubElement(root, 'mxCell')
                    edge.set('id', f'dep_edge_{source_id}_{target_id}')
                    edge.set('edge', '1')
                    edge.set('parent', '1')
                    edge.set('source', source_id)
                    edge.set('target', target_id)
                    
                    edge.set('style', 'endArrow=open;startArrow=none;dashed=1;html=1;' + 
                            'rounded=0;exitX=0;exitY=0.5;entryX=1;entryY=0.5;' +
                            'endFill=0;strokeWidth=1;')
                    
                    edge_geo = ET.SubElement(edge, 'mxGeometry')
                    edge_geo.set('relative', '1')
                    edge_geo.set('as', 'geometry')