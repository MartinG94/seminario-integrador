-- ======================================================================================
-- SGD-AVEIT — Módulo de Eventos, Asistencias y Apercibimientos (SCRUM-50 / Spec 005)
-- Archivo: docker/mysql/init/03-scrum50-eventos-asistencias-apercibimientos.sql
-- Propósito: Esquema de eventos, asistencias, convocados y control de llamados/felicitaciones
--            alineado 100% con las entidades preexistentes del sistema institucional de AVEIT:
--            - `tribunal_categoriaevento` (clasificación de eventos)
--            - `tribunal_evento` (reutilización de entidad legacy de eventos)
--            - `tribunal_evento_convocado` (nómina de socios citados a eventos)
--            - `tribunal_asistente` (reutilización de entidad legacy de asistencia)
--            - `atencionFelicitacion` (contadores de llamados de atención y felicitaciones con PK nroSocio)
-- ======================================================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- --------------------------------------------------------------------------------------
-- 1. CLASIFICACIÓN DE EVENTOS: tribunal_categoriaevento
-- --------------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS `tribunal_categoriaevento` (
  `idCategoria` int(11) NOT NULL AUTO_INCREMENT,
  `codigo` varchar(20) NOT NULL UNIQUE,
  `nombre` varchar(50) NOT NULL,
  PRIMARY KEY (`idCategoria`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `tribunal_categoriaevento` (`idCategoria`, `codigo`, `nombre`) VALUES
(1, 'REUNION', 'Reunión Institucional'),
(2, 'ACTIVIDAD', 'Actividad Operativa y Voluntariado')
ON DUPLICATE KEY UPDATE `nombre`=VALUES(`nombre`);

-- --------------------------------------------------------------------------------------
-- 2. TABLA DE EVENTOS INSTITUCIONALES: tribunal_evento
-- --------------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS `tribunal_evento` (
  `idEvento` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(128) NOT NULL,
  `descripcion` longtext NOT NULL,
  `categoria_id` int(11) DEFAULT 1,
  `categoria` varchar(20) NOT NULL DEFAULT 'REUNION',
  `tipo` varchar(30) NOT NULL DEFAULT 'ORDINARIA',
  `modalidad` varchar(30) NOT NULL DEFAULT 'PRESENCIAL_SEDE',
  `ubicacion` varchar(255) DEFAULT NULL,
  `lugar` varchar(200) NOT NULL DEFAULT 'Sede Central AVEIT',
  `fecha_publicacion` datetime(6) NOT NULL,
  `fechaHoraInicio` datetime(6) NOT NULL,
  `fechaHoraFin` datetime(6) DEFAULT NULL,
  `tieneHoraFin` tinyint(1) NOT NULL DEFAULT 0,
  `fecha_hora_cierre_efectivo` datetime(6) DEFAULT NULL,
  `fecha_reporte` datetime(6) DEFAULT NULL,
  `toleranciaLeveMinutos` smallint(5) unsigned NOT NULL DEFAULT 15,
  `toleranciaGraveMinutos` smallint(5) unsigned NOT NULL DEFAULT 30,
  `estado` varchar(30) NOT NULL DEFAULT 'PROGRAMADA',
  `estadoEvento_id` int(11) NOT NULL DEFAULT 1,
  `modo_convocatoria` varchar(30) NOT NULL DEFAULT 'PERSONALIZADA',
  `afectados_id` int(11) NOT NULL DEFAULT 20,
  `tipoEvento_id` int(11) DEFAULT NULL,
  `sancionPersonalizada_id` int(11) DEFAULT NULL,
  `grupo_convocado` varchar(10) DEFAULT NULL,
  `es_obligatoria` tinyint(1) NOT NULL DEFAULT 1,
  `es_sancionable` tinyint(1) NOT NULL DEFAULT 0,
  `motivo_no_sancionable` longtext DEFAULT NULL,
  `responsable_id` int(11) NOT NULL,
  `reportado_por_id` int(11) DEFAULT NULL,
  `subcomision_id` int(11) DEFAULT NULL,
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`idEvento`),
  KEY `fk_evento_afectados` (`afectados_id`),
  KEY `fk_evento_categoria` (`categoria_id`),
  KEY `fk_evento_tipoevento` (`tipoEvento_id`),
  KEY `fk_evento_responsable` (`responsable_id`),
  KEY `fk_evento_subcomision` (`subcomision_id`),
  KEY `fk_evento_reportado` (`reportado_por_id`),
  KEY `idx_evento_fechainicio_estado` (`fechaHoraInicio`, `estado`),
  KEY `idx_evento_cat_tipo_sanc` (`categoria`, `tipo`, `es_sancionable`),
  CONSTRAINT `chk_evento_publicacion_previa` CHECK (`fecha_publicacion` <= `fechaHoraInicio`),
  CONSTRAINT `chk_evento_fin_coherente` CHECK (`fechaHoraFin` IS NULL OR `fechaHoraFin` >= `fechaHoraInicio`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------------------------------------
-- 3. NÓMINA DE SOCIOS CITADOS / CONVOCADOS: tribunal_evento_convocado
-- --------------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS `tribunal_evento_convocado` (
  `idConvocado` int(11) NOT NULL AUTO_INCREMENT,
  `evento_id` int(11) NOT NULL,
  `socio_id` int(11) NOT NULL,
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`idConvocado`),
  UNIQUE KEY `unique_convocado_evento_socio` (`evento_id`, `socio_id`),
  KEY `fk_convocado_evento` (`evento_id`),
  KEY `fk_convocado_socio` (`socio_id`),
  CONSTRAINT `fk_convocado_evento` FOREIGN KEY (`evento_id`) REFERENCES `tribunal_evento` (`idEvento`) ON DELETE CASCADE,
  CONSTRAINT `fk_convocado_socio` FOREIGN KEY (`socio_id`) REFERENCES `socio_lista` (`nroSocio`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------------------------------------
-- 4. CONTROL DE ASISTENCIA: tribunal_asistente
-- --------------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS `tribunal_asistente` (
  `idAsistente` int(11) NOT NULL AUTO_INCREMENT,
  `evento_id` int(11) NOT NULL,
  `socio_id` int(11) NOT NULL,
  `fechaHoraLlegada` datetime(6) DEFAULT NULL,
  `fechaHoraSalida` datetime(6) DEFAULT NULL,
  `notificado` tinyint(1) NOT NULL DEFAULT 0,
  `fechaNotificacion` date DEFAULT NULL,
  `estado_asistencia` varchar(30) NOT NULL DEFAULT 'PRESENTE',
  `minutos_tardanza` int(10) unsigned NOT NULL DEFAULT 0,
  `minutos_retiro_anticipado` int(10) unsigned NOT NULL DEFAULT 0,
  `metodo_captura` varchar(20) NOT NULL DEFAULT 'MANUAL',
  `dispositivo_id` varchar(100) DEFAULT NULL,
  `motivo` longtext NOT NULL,
  `observaciones` longtext NOT NULL,
  `procesado_disciplinario` tinyint(1) NOT NULL DEFAULT 0,
  `expediente_generado_id` bigint(20) DEFAULT NULL,
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`idAsistente`),
  UNIQUE KEY `unique_asistente_per_evento_socio` (`evento_id`, `socio_id`),
  KEY `fk_asistente_evento` (`evento_id`),
  KEY `fk_asistente_socio` (`socio_id`),
  KEY `fk_asistente_expediente` (`expediente_generado_id`),
  CONSTRAINT `fk_asistente_evento` FOREIGN KEY (`evento_id`) REFERENCES `tribunal_evento` (`idEvento`) ON DELETE CASCADE,
  CONSTRAINT `fk_asistente_socio` FOREIGN KEY (`socio_id`) REFERENCES `socio_lista` (`nroSocio`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------------------------------------
-- 5. LIBRO DE CONTROL DE LLAMADOS Y FELICITACIONES: atencionFelicitacion
-- --------------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS `atencionFelicitacion` (
  `nroSocio` int(11) NOT NULL,
  `felicitaciones` int(11) NOT NULL DEFAULT 0,
  `llamadosAtencion` int(11) NOT NULL DEFAULT 0,
  PRIMARY KEY (`nroSocio`),
  CONSTRAINT `fk_atencionfel_socio` FOREIGN KEY (`nroSocio`) REFERENCES `socio_lista` (`nroSocio`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------------------------------------
-- 6. VISTAS DE INTEROPERABILIDAD Y COMPATIBILIDAD
-- --------------------------------------------------------------------------------------

DROP TABLE IF EXISTS `expedientes_registro_apercibimiento`;
DROP TABLE IF EXISTS `expedientes_asistencia_evento`;
DROP TABLE IF EXISTS `expedientes_evento`;

CREATE OR REPLACE VIEW `expedientes_evento` AS SELECT * FROM `tribunal_evento`;
CREATE OR REPLACE VIEW `expedientes_asistencia_evento` AS SELECT * FROM `tribunal_asistente`;
CREATE OR REPLACE VIEW `expedientes_evento_institucional` AS SELECT * FROM `tribunal_evento`;

SET FOREIGN_KEY_CHECKS = 1;
