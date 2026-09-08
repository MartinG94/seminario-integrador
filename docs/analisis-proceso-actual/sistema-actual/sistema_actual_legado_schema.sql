-- ======================================================================================
-- SISTEMA ACTUAL PREEXISTENTE (LEGADO / AS-IS) — A.V.E.I.T.
-- Archivo: sistema_actual_legado_schema.sql
-- Propósito: DDL físico completo y datos semilla para levantar el esquema MySQL 5.7 / 8.0
--            del sistema legado que el proyecto SGD-AVEIT viene a reemplazar.
-- Módulos cubiertos: `svaveit.socios` (padrón y satélites) y `svaveit.tribunal` (disciplina)
-- ======================================================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

CREATE DATABASE IF NOT EXISTS `svaveit` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `svaveit`;

-- --------------------------------------------------------------------------------------
-- 1. TABLAS DEL SISTEMA DE AUTENTICACIÓN (DJANGO AUTH BASE)
-- --------------------------------------------------------------------------------------

DROP TABLE IF EXISTS `auth_user`;
CREATE TABLE `auth_user` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL DEFAULT 0,
  `username` varchar(150) NOT NULL,
  `first_name` varchar(30) NOT NULL DEFAULT '',
  `last_name` varchar(150) NOT NULL DEFAULT '',
  `email` varchar(254) NOT NULL DEFAULT '',
  `is_staff` tinyint(1) NOT NULL DEFAULT 0,
  `is_active` tinyint(1) NOT NULL DEFAULT 1,
  `date_joined` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------------------------------------
-- 2. CATÁLOGOS DE LA APP SOCIOS (PADRÓN CENTRAL)
-- --------------------------------------------------------------------------------------

DROP TABLE IF EXISTS `socio_tipodocumento`;
CREATE TABLE `socio_tipodocumento` (
  `codTipoDoc` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(45) NOT NULL,
  `descripcion` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`codTipoDoc`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `socio_sexo`;
CREATE TABLE `socio_sexo` (
  `codSexo` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(45) NOT NULL,
  `descripcion` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`codSexo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `socio_tiposubcomision`;
CREATE TABLE `socio_tiposubcomision` (
  `codSubcomision` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(45) NOT NULL,
  PRIMARY KEY (`codSubcomision`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `socio_estadocivil`;
CREATE TABLE `socio_estadocivil` (
  `codEstadoCivil` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(45) NOT NULL,
  `descripcion` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`codEstadoCivil`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `socio_tipoSocio`;
CREATE TABLE `socio_tipoSocio` (
  `idTipoSocio` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(45) NOT NULL,
  PRIMARY KEY (`idTipoSocio`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `socio_estado`;
CREATE TABLE `socio_estado` (
  `codEstadoSocio` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(45) NOT NULL,
  `descripcion` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`codEstadoSocio`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `socio_motivoCambioEstado`;
CREATE TABLE `socio_motivoCambioEstado` (
  `idMotivoCambio` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(45) NOT NULL,
  `descripcion` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`idMotivoCambio`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `socio_especialidad`;
CREATE TABLE `socio_especialidad` (
  `codEspecialidad` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(45) NOT NULL,
  `descripcion` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`codEspecialidad`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `socio_tipoEstudioTurno`;
CREATE TABLE `socio_tipoEstudioTurno` (
  `codTipoEstudioTurno` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(45) NOT NULL,
  `descripcion` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`codTipoEstudioTurno`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `socio_tipodomicilio`;
CREATE TABLE `socio_tipodomicilio` (
  `codTipoDomicilio` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(45) NOT NULL,
  `descripcion` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`codTipoDomicilio`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `socio_tipotelefono`;
CREATE TABLE `socio_tipotelefono` (
  `codTipoTelefono` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(45) NOT NULL,
  `descripcion` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`codTipoTelefono`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `socio_tipomedio`;
CREATE TABLE `socio_tipomedio` (
  `codMedio` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(45) NOT NULL,
  `descripcion` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`codMedio`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `grupo_lista`;
CREATE TABLE `grupo_lista` (
  `nroGrupo` int(11) NOT NULL,
  `nombre` varchar(45) NOT NULL,
  `descripcion` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`nroGrupo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------------------------------------
-- 3. TABLA MATRIZ DE SOCIOS (`socio_lista`)
-- --------------------------------------------------------------------------------------

DROP TABLE IF EXISTS `socio_lista`;
CREATE TABLE `socio_lista` (
  `nroSocio` int(11) NOT NULL AUTO_INCREMENT,
  `apellido` varchar(45) NOT NULL,
  `nombre` varchar(45) NOT NULL,
  `fechaIngreso` date NOT NULL,
  `codTipoDoc` int(11) NOT NULL,
  `nroDoc` int(11) NOT NULL,
  `fechaNac` date NOT NULL,
  `codSexo` int(11) NOT NULL,
  `codSubcomision` int(11) NOT NULL,
  `codEstadoCivil` int(11) DEFAULT NULL,
  `fechaBaja` date DEFAULT NULL,
  `anoSocial` int(11) NOT NULL,
  `ingresante` tinyint(1) NOT NULL DEFAULT 0,
  `idTipoSocio` int(11) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `forzarCambioClave` tinyint(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`nroSocio`),
  KEY `fk_socio_tipodoc` (`codTipoDoc`),
  KEY `fk_socio_sexo` (`codSexo`),
  KEY `fk_socio_subcomision` (`codSubcomision`),
  KEY `fk_socio_estadocivil` (`codEstadoCivil`),
  KEY `fk_socio_tiposocio` (`idTipoSocio`),
  KEY `fk_socio_user` (`user_id`),
  CONSTRAINT `fk_socio_tipodoc` FOREIGN KEY (`codTipoDoc`) REFERENCES `socio_tipodocumento` (`codTipoDoc`),
  CONSTRAINT `fk_socio_sexo` FOREIGN KEY (`codSexo`) REFERENCES `socio_sexo` (`codSexo`),
  CONSTRAINT `fk_socio_subcomision` FOREIGN KEY (`codSubcomision`) REFERENCES `socio_tiposubcomision` (`codSubcomision`),
  CONSTRAINT `fk_socio_estadocivil` FOREIGN KEY (`codEstadoCivil`) REFERENCES `socio_estadocivil` (`codEstadoCivil`),
  CONSTRAINT `fk_socio_tiposocio` FOREIGN KEY (`idTipoSocio`) REFERENCES `socio_tipoSocio` (`idTipoSocio`),
  CONSTRAINT `fk_socio_user` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------------------------------------
-- 4. TABLAS SATÉLITE DE SOCIOS (CON ARTIFICIO compositeKey)
-- --------------------------------------------------------------------------------------

DROP TABLE IF EXISTS `socio_estadoHistorial`;
CREATE TABLE `socio_estadoHistorial` (
  `idEstadoHistorial` int(11) NOT NULL AUTO_INCREMENT,
  `idGrupo` int(11) NOT NULL,
  `nroSocio` int(11) NOT NULL,
  `fechaHora` datetime(6) NOT NULL,
  `codEstadoSocio` int(11) NOT NULL,
  `socio_motivoCambioEstado` int(11) NOT NULL,
  PRIMARY KEY (`idEstadoHistorial`),
  KEY `fk_historial_grupo` (`idGrupo`),
  KEY `fk_historial_socio` (`nroSocio`),
  KEY `fk_historial_estado` (`codEstadoSocio`),
  KEY `fk_historial_motivo` (`socio_motivoCambioEstado`),
  CONSTRAINT `fk_historial_grupo` FOREIGN KEY (`idGrupo`) REFERENCES `grupo_lista` (`nroGrupo`),
  CONSTRAINT `fk_historial_socio` FOREIGN KEY (`nroSocio`) REFERENCES `socio_lista` (`nroSocio`) ON DELETE CASCADE,
  CONSTRAINT `fk_historial_estado` FOREIGN KEY (`codEstadoSocio`) REFERENCES `socio_estado` (`codEstadoSocio`),
  CONSTRAINT `fk_historial_motivo` FOREIGN KEY (`socio_motivoCambioEstado`) REFERENCES `socio_motivoCambioEstado` (`idMotivoCambio`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `socio_estudio`;
CREATE TABLE `socio_estudio` (
  `compositeKey` int(11) NOT NULL,
  `nroSocio` int(11) NOT NULL,
  `nroLegajo` int(11) NOT NULL,
  `codEspecialidad` int(11) NOT NULL,
  `curso` varchar(10) DEFAULT NULL,
  `aula` varchar(10) DEFAULT NULL,
  `codTurno` int(11) DEFAULT NULL,
  PRIMARY KEY (`compositeKey`),
  KEY `fk_estudio_socio` (`nroSocio`),
  KEY `fk_estudio_especialidad` (`codEspecialidad`),
  KEY `fk_estudio_turno` (`codTurno`),
  CONSTRAINT `fk_estudio_socio` FOREIGN KEY (`nroSocio`) REFERENCES `socio_lista` (`nroSocio`) ON DELETE CASCADE,
  CONSTRAINT `fk_estudio_especialidad` FOREIGN KEY (`codEspecialidad`) REFERENCES `socio_especialidad` (`codEspecialidad`),
  CONSTRAINT `fk_estudio_turno` FOREIGN KEY (`codTurno`) REFERENCES `socio_tipoEstudioTurno` (`codTipoEstudioTurno`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `socio_email`;
CREATE TABLE `socio_email` (
  `compositeKey` int(11) NOT NULL,
  `nroSocio` int(11) NOT NULL,
  `idEmail` int(11) NOT NULL,
  `email` varchar(45) NOT NULL,
  `comprobado` tinyint(1) NOT NULL DEFAULT 0,
  `habilitado` tinyint(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`compositeKey`),
  KEY `fk_email_socio` (`nroSocio`),
  CONSTRAINT `fk_email_socio` FOREIGN KEY (`nroSocio`) REFERENCES `socio_lista` (`nroSocio`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `socio_telefono`;
CREATE TABLE `socio_telefono` (
  `compositeKey` int(11) NOT NULL,
  `nroSocio` int(11) NOT NULL,
  `idTelefono` int(11) NOT NULL,
  `telefono` varchar(45) NOT NULL,
  `codTipoTelefono` int(11) NOT NULL,
  PRIMARY KEY (`compositeKey`),
  KEY `fk_tel_socio` (`nroSocio`),
  KEY `fk_tel_tipo` (`codTipoTelefono`),
  CONSTRAINT `fk_tel_socio` FOREIGN KEY (`nroSocio`) REFERENCES `socio_lista` (`nroSocio`) ON DELETE CASCADE,
  CONSTRAINT `fk_tel_tipo` FOREIGN KEY (`codTipoTelefono`) REFERENCES `socio_tipotelefono` (`codTipoTelefono`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `socio_domicilio`;
CREATE TABLE `socio_domicilio` (
  `compositeKey` int(11) NOT NULL,
  `nroSocio` int(11) NOT NULL,
  `direccion` varchar(256) DEFAULT NULL,
  `barrio` varchar(45) DEFAULT NULL,
  `ciudad` varchar(45) NOT NULL,
  `provincia` varchar(45) NOT NULL,
  `codTipoDomicilio` int(11) NOT NULL,
  PRIMARY KEY (`compositeKey`),
  KEY `fk_dom_socio` (`nroSocio`),
  KEY `fk_dom_tipo` (`codTipoDomicilio`),
  CONSTRAINT `fk_dom_socio` FOREIGN KEY (`nroSocio`) REFERENCES `socio_lista` (`nroSocio`) ON DELETE CASCADE,
  CONSTRAINT `fk_dom_tipo` FOREIGN KEY (`codTipoDomicilio`) REFERENCES `socio_tipodomicilio` (`codTipoDomicilio`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `socio_medio`;
CREATE TABLE `socio_medio` (
  `compositeKey` int(11) NOT NULL,
  `nroSocio` int(11) NOT NULL,
  `codMedio` int(11) NOT NULL,
  `descripcion` varchar(45) NOT NULL,
  PRIMARY KEY (`compositeKey`),
  KEY `fk_medio_socio` (`nroSocio`),
  KEY `fk_medio_tipo` (`codMedio`),
  CONSTRAINT `fk_medio_socio` FOREIGN KEY (`nroSocio`) REFERENCES `socio_lista` (`nroSocio`) ON DELETE CASCADE,
  CONSTRAINT `fk_medio_tipo` FOREIGN KEY (`codMedio`) REFERENCES `socio_tipomedio` (`codMedio`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `socio_induccion`;
CREATE TABLE `socio_induccion` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nroSocio` int(11) NOT NULL,
  `codSubcomision` int(11) NOT NULL,
  `orden` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_ind_socio` (`nroSocio`),
  KEY `fk_ind_subcomision` (`codSubcomision`),
  CONSTRAINT `fk_ind_socio` FOREIGN KEY (`nroSocio`) REFERENCES `socio_lista` (`nroSocio`) ON DELETE CASCADE,
  CONSTRAINT `fk_ind_subcomision` FOREIGN KEY (`codSubcomision`) REFERENCES `socio_tiposubcomision` (`codSubcomision`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `socio_induccionencuesta`;
CREATE TABLE `socio_induccionencuesta` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nroSocio` int(11) NOT NULL,
  `codSubcomision` int(11) NOT NULL,
  `porcentaje` double NOT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_indenc_socio` (`nroSocio`),
  KEY `fk_indenc_subcomision` (`codSubcomision`),
  CONSTRAINT `fk_indenc_socio` FOREIGN KEY (`nroSocio`) REFERENCES `socio_lista` (`nroSocio`) ON DELETE CASCADE,
  CONSTRAINT `fk_indenc_subcomision` FOREIGN KEY (`codSubcomision`) REFERENCES `socio_tiposubcomision` (`codSubcomision`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------------------------------------
-- 5. CATÁLOGOS DE LA APP TRIBUNAL DE DISCIPLINA
-- --------------------------------------------------------------------------------------

DROP TABLE IF EXISTS `tribunal_afectados`;
CREATE TABLE `tribunal_afectados` (
  `idAfectados` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(30) NOT NULL,
  `descripcion` varchar(80) NOT NULL,
  PRIMARY KEY (`idAfectados`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `tribunal_estadoevento`;
CREATE TABLE `tribunal_estadoevento` (
  `idEstadoEvento` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(30) NOT NULL,
  `descripcion` varchar(80) NOT NULL,
  PRIMARY KEY (`idEstadoEvento`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `tribunal_estadoexpediente`;
CREATE TABLE `tribunal_estadoexpediente` (
  `idEstadoExpediente` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(30) NOT NULL,
  `descripcion` varchar(80) NOT NULL,
  PRIMARY KEY (`idEstadoExpediente`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `tribunal_estadojustificacion`;
CREATE TABLE `tribunal_estadojustificacion` (
  `idEstadoJustificacion` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(30) NOT NULL,
  `descripcion` varchar(80) NOT NULL,
  PRIMARY KEY (`idEstadoJustificacion`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `tribunal_estadodisposicion`;
CREATE TABLE `tribunal_estadodisposicion` (
  `idEstadoDisposicion` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(30) NOT NULL,
  `descripcion` varchar(80) NOT NULL,
  PRIMARY KEY (`idEstadoDisposicion`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `tribunal_tiposancion`;
CREATE TABLE `tribunal_tiposancion` (
  `idTipoSancion` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(30) NOT NULL,
  `descripcion` varchar(80) NOT NULL,
  PRIMARY KEY (`idTipoSancion`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `tribunal_justificacion`;
CREATE TABLE `tribunal_justificacion` (
  `idJustificacion` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(30) NOT NULL,
  `descripcion` varchar(80) NOT NULL,
  PRIMARY KEY (`idJustificacion`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `tribunal_valorsancion`;
CREATE TABLE `tribunal_valorsancion` (
  `idSancion` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(30) NOT NULL,
  `valor` double NOT NULL,
  PRIMARY KEY (`idSancion`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `tribunal_reglamento`;
CREATE TABLE `tribunal_reglamento` (
  `idReglamento` int(11) NOT NULL AUTO_INCREMENT,
  `titulo` varchar(45) NOT NULL,
  `seccion` int(11) NOT NULL,
  `articulo` int(11) NOT NULL,
  `inciso` varchar(11) NOT NULL DEFAULT '-',
  `descripcion` longtext DEFAULT NULL,
  PRIMARY KEY (`idReglamento`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `tribunal_tipoevento`;
CREATE TABLE `tribunal_tipoevento` (
  `idTipoEvento` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(128) NOT NULL,
  `sancionFalta_id` int(11) NOT NULL,
  `sancionLeve_id` int(11) NOT NULL,
  `sancionGrave_id` int(11) NOT NULL,
  PRIMARY KEY (`idTipoEvento`),
  KEY `fk_tipoevento_falta` (`sancionFalta_id`),
  KEY `fk_tipoevento_leve` (`sancionLeve_id`),
  KEY `fk_tipoevento_grave` (`sancionGrave_id`),
  CONSTRAINT `fk_tipoevento_falta` FOREIGN KEY (`sancionFalta_id`) REFERENCES `tribunal_valorsancion` (`idSancion`),
  CONSTRAINT `fk_tipoevento_leve` FOREIGN KEY (`sancionLeve_id`) REFERENCES `tribunal_valorsancion` (`idSancion`),
  CONSTRAINT `fk_tipoevento_grave` FOREIGN KEY (`sancionGrave_id`) REFERENCES `tribunal_valorsancion` (`idSancion`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `tribunal_sancionpersonalizadaeventos`;
CREATE TABLE `tribunal_sancionpersonalizadaeventos` (
  `idSancionPersonalizada` int(11) NOT NULL AUTO_INCREMENT,
  `sancionFaltaPersonalizada_id` int(11) NOT NULL,
  `sancionLevePersonalizada_id` int(11) NOT NULL,
  `sancionGravePersonalizada_id` int(11) NOT NULL,
  PRIMARY KEY (`idSancionPersonalizada`),
  KEY `fk_sancionp_falta` (`sancionFaltaPersonalizada_id`),
  KEY `fk_sancionp_leve` (`sancionLevePersonalizada_id`),
  KEY `fk_sancionp_grave` (`sancionGravePersonalizada_id`),
  CONSTRAINT `fk_sancionp_falta` FOREIGN KEY (`sancionFaltaPersonalizada_id`) REFERENCES `tribunal_valorsancion` (`idSancion`),
  CONSTRAINT `fk_sancionp_leve` FOREIGN KEY (`sancionLevePersonalizada_id`) REFERENCES `tribunal_valorsancion` (`idSancion`),
  CONSTRAINT `fk_sancionp_grave` FOREIGN KEY (`sancionGravePersonalizada_id`) REFERENCES `tribunal_valorsancion` (`idSancion`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------------------------------------
-- 6. TABLAS OPERATIVAS DEL MÓDULO TRIBUNAL
-- --------------------------------------------------------------------------------------

DROP TABLE IF EXISTS `tribunal_evento`;
CREATE TABLE `tribunal_evento` (
  `idEvento` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(128) NOT NULL,
  `afectados_id` int(11) NOT NULL,
  `fechaHoraInicio` datetime(6) DEFAULT NULL,
  `fechaHoraFin` datetime(6) DEFAULT NULL,
  `tieneHoraFin` tinyint(1) NOT NULL DEFAULT 0,
  `responsable_id` int(11) NOT NULL,
  `estadoEvento_id` int(11) NOT NULL,
  `tipoEvento_id` int(11) DEFAULT NULL,
  `sancionPersonalizada_id` int(11) DEFAULT NULL,
  `toleranciaLeveMinutos` int(10) unsigned NOT NULL DEFAULT 15,
  `toleranciaGraveMinutos` int(10) unsigned NOT NULL DEFAULT 30,
  PRIMARY KEY (`idEvento`),
  KEY `fk_evento_afectados` (`afectados_id`),
  KEY `fk_evento_responsable` (`responsable_id`),
  KEY `fk_evento_estado` (`estadoEvento_id`),
  KEY `fk_evento_tipoevento` (`tipoEvento_id`),
  KEY `fk_evento_sancionp` (`sancionPersonalizada_id`),
  CONSTRAINT `fk_evento_afectados` FOREIGN KEY (`afectados_id`) REFERENCES `tribunal_afectados` (`idAfectados`),
  CONSTRAINT `fk_evento_responsable` FOREIGN KEY (`responsable_id`) REFERENCES `socio_lista` (`nroSocio`),
  CONSTRAINT `fk_evento_estado` FOREIGN KEY (`estadoEvento_id`) REFERENCES `tribunal_estadoevento` (`idEstadoEvento`),
  CONSTRAINT `fk_evento_tipoevento` FOREIGN KEY (`tipoEvento_id`) REFERENCES `tribunal_tipoevento` (`idTipoEvento`),
  CONSTRAINT `fk_evento_sancionp` FOREIGN KEY (`sancionPersonalizada_id`) REFERENCES `tribunal_sancionpersonalizadaeventos` (`idSancionPersonalizada`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `tribunal_asistente`;
CREATE TABLE `tribunal_asistente` (
  `idAsistente` int(11) NOT NULL AUTO_INCREMENT,
  `evento_id` int(11) NOT NULL,
  `socio_id` int(11) NOT NULL,
  `fechaHoraLlegada` datetime(6) DEFAULT NULL,
  `fechaHoraSalida` datetime(6) DEFAULT NULL,
  `notificado` tinyint(1) NOT NULL DEFAULT 0,
  `fechaNotificacion` date DEFAULT NULL,
  PRIMARY KEY (`idAsistente`),
  KEY `fk_asistente_evento` (`evento_id`),
  KEY `fk_asistente_socio` (`socio_id`),
  CONSTRAINT `fk_asistente_evento` FOREIGN KEY (`evento_id`) REFERENCES `tribunal_evento` (`idEvento`),
  CONSTRAINT `fk_asistente_socio` FOREIGN KEY (`socio_id`) REFERENCES `socio_lista` (`nroSocio`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `tribunal_solicitud`;
CREATE TABLE `tribunal_solicitud` (
  `idSolicitud` int(11) NOT NULL AUTO_INCREMENT,
  `fechaHora` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  `titulo` longtext NOT NULL,
  `motivoSancion` longtext NOT NULL,
  `responsable_id` int(11) NOT NULL,
  `sancionSolicitada_id` int(11) NOT NULL,
  `reglamento` varchar(300) NOT NULL,
  PRIMARY KEY (`idSolicitud`),
  KEY `fk_solicitud_responsable` (`responsable_id`),
  KEY `fk_solicitud_valorsancion` (`sancionSolicitada_id`),
  CONSTRAINT `fk_solicitud_responsable` FOREIGN KEY (`responsable_id`) REFERENCES `socio_lista` (`nroSocio`),
  CONSTRAINT `fk_solicitud_valorsancion` FOREIGN KEY (`sancionSolicitada_id`) REFERENCES `tribunal_valorsancion` (`idSancion`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `tribunal_datosresolucion`;
CREATE TABLE `tribunal_datosresolucion` (
  `idDatosResolucion` int(11) NOT NULL AUTO_INCREMENT,
  `reglamento1` varchar(300) NOT NULL,
  `reglamento2` varchar(300) DEFAULT NULL,
  `reglamento3` varchar(300) DEFAULT NULL,
  `responsable1_id` int(11) DEFAULT NULL,
  `responsable2_id` int(11) DEFAULT NULL,
  `responsable3_id` int(11) DEFAULT NULL,
  `responsable1Text` varchar(128) DEFAULT NULL,
  `responsable2Text` varchar(128) DEFAULT NULL,
  `responsable3Text` varchar(128) DEFAULT NULL,
  `consideracion` longtext NOT NULL,
  PRIMARY KEY (`idDatosResolucion`),
  KEY `fk_datosres_resp1` (`responsable1_id`),
  KEY `fk_datosres_resp2` (`responsable2_id`),
  KEY `fk_datosres_resp3` (`responsable3_id`),
  CONSTRAINT `fk_datosres_resp1` FOREIGN KEY (`responsable1_id`) REFERENCES `socio_lista` (`nroSocio`) ON DELETE SET NULL,
  CONSTRAINT `fk_datosres_resp2` FOREIGN KEY (`responsable2_id`) REFERENCES `socio_lista` (`nroSocio`) ON DELETE SET NULL,
  CONSTRAINT `fk_datosres_resp3` FOREIGN KEY (`responsable3_id`) REFERENCES `socio_lista` (`nroSocio`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `tribunal_expediente`;
CREATE TABLE `tribunal_expediente` (
  `idExpediente` int(11) NOT NULL AUTO_INCREMENT,
  `nroExpediente` varchar(9) NOT NULL,
  `estadoExpediente_id` int(11) DEFAULT NULL,
  `solicitud_id` int(11) DEFAULT NULL,
  `evento_id` int(11) DEFAULT NULL,
  `tipoSancion_id` int(11) DEFAULT NULL,
  `fechaHora` datetime(6) DEFAULT CURRENT_TIMESTAMP(6),
  `puntos_id` int(11) NOT NULL,
  `dataRes_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`idExpediente`),
  KEY `fk_expediente_estado` (`estadoExpediente_id`),
  KEY `fk_expediente_solicitud` (`solicitud_id`),
  KEY `fk_expediente_evento` (`evento_id`),
  KEY `fk_expediente_tiposancion` (`tipoSancion_id`),
  KEY `fk_expediente_puntos` (`puntos_id`),
  KEY `fk_expediente_datares` (`dataRes_id`),
  CONSTRAINT `fk_expediente_estado` FOREIGN KEY (`estadoExpediente_id`) REFERENCES `tribunal_estadoexpediente` (`idEstadoExpediente`),
  CONSTRAINT `fk_expediente_solicitud` FOREIGN KEY (`solicitud_id`) REFERENCES `tribunal_solicitud` (`idSolicitud`) ON DELETE SET NULL,
  CONSTRAINT `fk_expediente_evento` FOREIGN KEY (`evento_id`) REFERENCES `tribunal_evento` (`idEvento`) ON DELETE SET NULL,
  CONSTRAINT `fk_expediente_tiposancion` FOREIGN KEY (`tipoSancion_id`) REFERENCES `tribunal_tiposancion` (`idTipoSancion`),
  CONSTRAINT `fk_expediente_puntos` FOREIGN KEY (`puntos_id`) REFERENCES `tribunal_valorsancion` (`idSancion`),
  CONSTRAINT `fk_expediente_datares` FOREIGN KEY (`dataRes_id`) REFERENCES `tribunal_datosresolucion` (`idDatosResolucion`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `tribunal_sancion`;
CREATE TABLE `tribunal_sancion` (
  `idSancion` int(11) NOT NULL AUTO_INCREMENT,
  `socio_id` int(11) NOT NULL,
  `expediente_id` int(11) NOT NULL,
  `estadoJustificacion_id` int(11) NOT NULL,
  `fechaLimiteEnvio` datetime(6) DEFAULT NULL,
  `notificacionSancion` tinyint(1) NOT NULL DEFAULT 0,
  `aprobada` tinyint(1) NOT NULL DEFAULT 0,
  `responsable_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`idSancion`),
  KEY `fk_sancion_socio` (`socio_id`),
  KEY `fk_sancion_expediente` (`expediente_id`),
  KEY `fk_sancion_estadojust` (`estadoJustificacion_id`),
  KEY `fk_sancion_responsable` (`responsable_id`),
  CONSTRAINT `fk_sancion_socio` FOREIGN KEY (`socio_id`) REFERENCES `socio_lista` (`nroSocio`),
  CONSTRAINT `fk_sancion_expediente` FOREIGN KEY (`expediente_id`) REFERENCES `tribunal_expediente` (`idExpediente`) ON DELETE CASCADE,
  CONSTRAINT `fk_sancion_estadojust` FOREIGN KEY (`estadoJustificacion_id`) REFERENCES `tribunal_estadojustificacion` (`idEstadoJustificacion`),
  CONSTRAINT `fk_sancion_responsable` FOREIGN KEY (`responsable_id`) REFERENCES `socio_lista` (`nroSocio`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `tribunal_t02`;
CREATE TABLE `tribunal_t02` (
  `idT02` int(11) NOT NULL AUTO_INCREMENT,
  `justificacion_id` int(11) NOT NULL,
  `observacion` varchar(400) DEFAULT NULL,
  `socio_id` int(11) NOT NULL,
  `sancion_id` int(11) NOT NULL,
  `fechaHora` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  `justificativo` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`idT02`),
  KEY `fk_t02_justificacion` (`justificacion_id`),
  KEY `fk_t02_socio` (`socio_id`),
  KEY `fk_t02_sancion` (`sancion_id`),
  CONSTRAINT `fk_t02_justificacion` FOREIGN KEY (`justificacion_id`) REFERENCES `tribunal_justificacion` (`idJustificacion`),
  CONSTRAINT `fk_t02_socio` FOREIGN KEY (`socio_id`) REFERENCES `socio_lista` (`nroSocio`),
  CONSTRAINT `fk_t02_sancion` FOREIGN KEY (`sancion_id`) REFERENCES `tribunal_sancion` (`idSancion`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `tribunal_t03`;
CREATE TABLE `tribunal_t03` (
  `idT03` int(11) NOT NULL AUTO_INCREMENT,
  `justificacion` longtext NOT NULL,
  `socio_id` int(11) NOT NULL,
  `sancion_id` int(11) NOT NULL,
  `fechaHora` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  `justificativo` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`idT03`),
  KEY `fk_t03_socio` (`socio_id`),
  KEY `fk_t03_sancion` (`sancion_id`),
  CONSTRAINT `fk_t03_socio` FOREIGN KEY (`socio_id`) REFERENCES `socio_lista` (`nroSocio`),
  CONSTRAINT `fk_t03_sancion` FOREIGN KEY (`sancion_id`) REFERENCES `tribunal_sancion` (`idSancion`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `tribunal_disposicion`;
CREATE TABLE `tribunal_disposicion` (
  `idDisposicion` int(11) NOT NULL AUTO_INCREMENT,
  `nroDisposicion` varchar(9) NOT NULL,
  `expediente_id` int(11) NOT NULL,
  `fechaHora` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `estadoDisposicion_id` int(11) NOT NULL,
  `responsable1_id` int(11) NOT NULL,
  `responsable2_id` int(11) DEFAULT NULL,
  `responsable3_id` int(11) DEFAULT NULL,
  `responsable1Text` varchar(128) DEFAULT NULL,
  `responsable2Text` varchar(128) DEFAULT NULL,
  `responsable3Text` varchar(128) DEFAULT NULL,
  `resolucion` longtext NOT NULL,
  `reglamento` varchar(300) NOT NULL,
  PRIMARY KEY (`idDisposicion`),
  KEY `fk_disp_expediente` (`expediente_id`),
  KEY `fk_disp_estado` (`estadoDisposicion_id`),
  KEY `fk_disp_resp1` (`responsable1_id`),
  KEY `fk_disp_resp2` (`responsable2_id`),
  KEY `fk_disp_resp3` (`responsable3_id`),
  CONSTRAINT `fk_disp_expediente` FOREIGN KEY (`expediente_id`) REFERENCES `tribunal_expediente` (`idExpediente`),
  CONSTRAINT `fk_disp_estado` FOREIGN KEY (`estadoDisposicion_id`) REFERENCES `tribunal_estadodisposicion` (`idEstadoDisposicion`),
  CONSTRAINT `fk_disp_resp1` FOREIGN KEY (`responsable1_id`) REFERENCES `socio_lista` (`nroSocio`),
  CONSTRAINT `fk_disp_resp2` FOREIGN KEY (`responsable2_id`) REFERENCES `socio_lista` (`nroSocio`) ON DELETE SET NULL,
  CONSTRAINT `fk_disp_resp3` FOREIGN KEY (`responsable3_id`) REFERENCES `socio_lista` (`nroSocio`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `tribunal_enmendado`;
CREATE TABLE `tribunal_enmendado` (
  `idEnmendado` int(11) NOT NULL AUTO_INCREMENT,
  `disposicion_id` int(11) NOT NULL,
  `socio_id` int(11) NOT NULL,
  `notificado` tinyint(1) NOT NULL DEFAULT 0,
  `justificacion` longtext NOT NULL,
  PRIMARY KEY (`idEnmendado`),
  KEY `fk_enm_disposicion` (`disposicion_id`),
  KEY `fk_enm_socio` (`socio_id`),
  CONSTRAINT `fk_enm_disposicion` FOREIGN KEY (`disposicion_id`) REFERENCES `tribunal_disposicion` (`idDisposicion`),
  CONSTRAINT `fk_enm_socio` FOREIGN KEY (`socio_id`) REFERENCES `socio_lista` (`nroSocio`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `tribunal_puntajeaplicado`;
CREATE TABLE `tribunal_puntajeaplicado` (
  `idPuntajeAplicado` int(11) NOT NULL AUTO_INCREMENT,
  `puntajeAplicado` double NOT NULL,
  `socio_id` int(11) NOT NULL,
  `expediente_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`idPuntajeAplicado`),
  KEY `fk_ptjaplicado_socio` (`socio_id`),
  KEY `fk_ptjaplicado_expediente` (`expediente_id`),
  CONSTRAINT `fk_ptjaplicado_socio` FOREIGN KEY (`socio_id`) REFERENCES `socio_lista` (`nroSocio`),
  CONSTRAINT `fk_ptjaplicado_expediente` FOREIGN KEY (`expediente_id`) REFERENCES `tribunal_expediente` (`idExpediente`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `tribunal_puntajegeneral`;
CREATE TABLE `tribunal_puntajegeneral` (
  `idPuntajeGeneral` int(11) NOT NULL AUTO_INCREMENT,
  `socio_id` int(11) NOT NULL,
  `puntos` double NOT NULL DEFAULT 0,
  `felicitaciones` int(11) NOT NULL DEFAULT 0,
  `llamadosAtencion` int(11) NOT NULL DEFAULT 0,
  PRIMARY KEY (`idPuntajeGeneral`),
  UNIQUE KEY `socio_id_unique` (`socio_id`),
  CONSTRAINT `fk_ptjgral_socio` FOREIGN KEY (`socio_id`) REFERENCES `socio_lista` (`nroSocio`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------------------------------------
-- 7. CARGA DE DATOS SEMILLA / CATÁLOGOS INSTITUCIONALES OFICIALES (CONSTANTES HISTÓRICAS)
-- --------------------------------------------------------------------------------------

-- 7.1 Tipos de Documento
INSERT INTO `socio_tipodocumento` (`codTipoDoc`, `nombre`, `descripcion`) VALUES
(1, 'DNI', 'Documento Nacional de Identidad'),
(2, 'Pasaporte', 'Pasaporte Internacional'),
(3, 'LC', 'Libreta Cívica'),
(4, 'LE', 'Libreta de Enrolamiento');

-- 7.2 Sexos
INSERT INTO `socio_sexo` (`codSexo`, `nombre`, `descripcion`) VALUES
(1, 'Masculino', 'Masculino'),
(2, 'Femenino', 'Femenino'),
(3, 'Otro', 'No binario / Otro');

-- 7.3 Estados Civiles
INSERT INTO `socio_estadocivil` (`codEstadoCivil`, `nombre`, `descripcion`) VALUES
(1, 'Soltero/a', 'Soltero o soltera'),
(2, 'Casado/a', 'Casado o casada'),
(3, 'Divorciado/a', 'Divorciado o divorciada'),
(4, 'Viudo/a', 'Viudo o viuda');

-- 7.4 Subcomisiones Oficiales (const_id_tipo_subcomision en constants.py)
INSERT INTO `socio_tiposubcomision` (`codSubcomision`, `nombre`) VALUES
(1, 'Cómputos'),
(2, 'Recursos Humanos'),
(3, 'Relaciones Institucionales'),
(4, 'Prensa'),
(5, 'Mantenimiento'),
(6, 'Gestión Social y Ambiental'),
(7, 'Eventos'),
(8, 'Rifas'),
(9, 'Comisión Directiva'),
(10, 'Tribunal de Disciplina'),
(11, 'Ex Viajeros'),
(99, 'Sin Subcomisión');

-- 7.5 Cargos Estatutarios / TipoSocio (const_id_tipo_socio en constants.py)
INSERT INTO `socio_tipoSocio` (`idTipoSocio`, `nombre`) VALUES
(1, 'Presidente Subcomisión'),
(2, 'Vicepresidente Subcomisión'),
(3, 'Presidente AVEIT'),
(4, 'Vicepresidente AVEIT'),
(5, 'Tesorero'),
(6, 'Protesorero'),
(7, 'Secretario de Actas'),
(8, 'Secretario General'),
(9, 'Prosecretario'),
(10, 'Titular Tribunal'),
(11, 'Suplente Tribunal'),
(12, 'Socio Ordinario'),
(13, 'Secretario'),
(14, 'Revisor de cuentas'),
(15, 'Revisor de cuentas suplente');

-- 7.6 Estados Sociales
INSERT INTO `socio_estado` (`codEstadoSocio`, `nombre`, `descripcion`) VALUES
(1, 'Activo', 'Socio activo con plenos derechos'),
(2, 'Pasivo', 'Socio pasivo en receso justificado'),
(3, 'Impasivo', 'Socio con mora transitoria'),
(4, 'Inactivo', 'Socio inactivo en proceso de baja'),
(5, 'Baja', 'Socio dado de baja');

-- 7.7 Motivos de Cambio de Estado Social
INSERT INTO `socio_motivoCambioEstado` (`idMotivoCambio`, `nombre`, `descripcion`) VALUES
(1, 'Regular', 'Evolución normal de membresía'),
(2, 'Licencia Académica', 'Licencia por exámenes o cursado'),
(3, 'Licencia Laboral', 'Licencia por compromisos de trabajo'),
(4, 'Sanción Disciplinaria', 'Suspensión impuesta por el Tribunal'),
(5, 'Renuncia Voluntaria', 'Desvinculación a pedido del socio');

-- 7.8 Especialidades Académicas
INSERT INTO `socio_especialidad` (`codEspecialidad`, `nombre`, `descripcion`) VALUES
(1, 'Ingeniería en Sistemas de Información', 'UTN FRC'),
(2, 'Ingeniería Química', 'UTN FRC'),
(3, 'Ingeniería Mecánica', 'UTN FRC'),
(4, 'Ingeniería Eléctrica', 'UTN FRC'),
(5, 'Ingeniería Electrónica', 'UTN FRC'),
(6, 'Ingeniería Industrial', 'UTN FRC'),
(7, 'Ingeniería Civil', 'UTN FRC');

-- 7.9 Turnos de Estudio
INSERT INTO `socio_tipoEstudioTurno` (`codTipoEstudioTurno`, `nombre`, `descripcion`) VALUES
(1, 'Mañana', 'Turno mañana (08:00 a 13:00)'),
(2, 'Tarde', 'Turno tarde (13:30 a 18:30)'),
(3, 'Noche', 'Turno noche (18:45 a 23:15)');

-- 7.10 Tipos de Domicilio
INSERT INTO `socio_tipodomicilio` (`codTipoDomicilio`, `nombre`, `descripcion`) VALUES
(1, 'Particular Córdoba', 'Residencia en Córdoba Capital'),
(2, 'Familiar Origen', 'Domicilio de procedencia familiar'),
(3, 'Laboral', 'Lugar de trabajo');

-- 7.11 Tipos de Teléfono
INSERT INTO `socio_tipotelefono` (`codTipoTelefono`, `nombre`, `descripcion`) VALUES
(1, 'Celular', 'Teléfono móvil personal'),
(2, 'Familiar', 'Teléfono de contacto de emergencia'),
(3, 'Fijo', 'Línea de red fija');

-- 7.12 Redes Sociales / Medios
INSERT INTO `socio_tipomedio` (`codMedio`, `nombre`, `descripcion`) VALUES
(1, 'Instagram', '@usuario'),
(2, 'LinkedIn', 'URL de perfil profesional'),
(3, 'GitHub', 'Usuario de desarrollo'),
(4, 'Twitter/X', '@usuario');

-- 7.13 Grupos Sociales Históricos
INSERT INTO `grupo_lista` (`nroGrupo`, `nombre`, `descripcion`) VALUES
(53, 'Grupo 53', 'Cohorte Social 2020'),
(54, 'Grupo 54', 'Cohorte Social 2021'),
(55, 'Grupo 55', 'Cohorte Social 2022'),
(56, 'Grupo 56', 'Cohorte Social 2023');

-- 7.14 Afectados del Tribunal (const_id_afectados en constants.py)
INSERT INTO `tribunal_afectados` (`idAfectados`, `nombre`, `descripcion`) VALUES
(1, 'Comisión Directiva', 'Mesa Ejecutiva de CD'),
(2, 'Cómputos', 'Subcomisión de Cómputos y Sistemas'),
(3, 'Recursos Humanos', 'Subcomisión de RRHH'),
(4, 'Relaciones Institucionales', 'Subcomisión de RII'),
(5, 'Prensa y Difusión', 'Subcomisión de Prensa'),
(6, 'Mantenimiento', 'Subcomisión de Mantenimiento Edilicio'),
(7, 'Gestión Social y Ambiental', 'Subcomisión de GSA'),
(8, 'Organización y Eventos', 'Subcomisión de Eventos'),
(9, 'Rifas', 'Subcomisión de Rifas'),
(10, 'Tribunal de Disciplina', 'Órgano Jurisdiccional'),
(20, 'Aveit', 'Todos los socios de la Asociación'),
(21, 'xSocios', 'Convocatoria nominal ad-hoc'),
(53, 'G53', 'Cohorte G53'),
(54, 'G54', 'Cohorte G54'),
(55, 'G55', 'Cohorte G55'),
(56, 'G56', 'Cohorte G56');

-- 7.15 Estados de Evento
INSERT INTO `tribunal_estadoevento` (`idEstadoEvento`, `nombre`, `descripcion`) VALUES
(1, 'PorNotificar', 'Evento cerrado pendiente de emisión de avisos'),
(2, 'Esperando', 'Avisos emitidos, esperando descargo preliminar'),
(3, 'PorSancionar', 'En trámite de imputación ante el Tribunal'),
(4, 'Emitido', 'Sanciones labradas y finalizadas');

-- 7.16 Estados del Expediente (Los 6 Estados Oficiales del Reglamento)
INSERT INTO `tribunal_estadoexpediente` (`idEstadoExpediente`, `nombre`, `descripcion`) VALUES
(1, 'Creado', 'Expediente caratulado sin traslado aún'),
(2, 'Justificando', 'Plazo de 5 días hábiles abierto para T02/T03'),
(3, 'EnRevision', 'Tribunal deliberando sobre pruebas y descargos'),
(4, 'PorEmitir', 'Fallo redactado, pendiente de firmas colegiadas'),
(5, 'MailPendiente', 'Fallo firmado, en cola de notificación SMTP'),
(6, 'Emitido', 'Disposición notificada y puntos aplicados');

-- 7.17 Estados de Justificación
INSERT INTO `tribunal_estadojustificacion` (`idEstadoJustificacion`, `nombre`, `descripcion`) VALUES
(1, 'Pendiente', 'Descargo no presentado o sin revisar'),
(2, 'EnRevision', 'Tribunal analizando el descargo'),
(3, 'Aprobada', 'Descargo admitido eximente de sanción'),
(4, 'Desaprobada', 'Descargo rechazado, se ratifica sanción');

-- 7.18 Estados de Disposición
INSERT INTO `tribunal_estadodisposicion` (`idEstadoDisposicion`, `nombre`, `descripcion`) VALUES
(1, 'Creada', 'Borrador de resolución redactado'),
(2, 'Emitida', 'Resolución formal firmada y promulgada');

-- 7.19 Tipos de Sanción
INSERT INTO `tribunal_tiposancion` (`idTipoSancion`, `nombre`, `descripcion`) VALUES
(1, 'LlegaTardeLeve', 'Demora de 15 a 30 minutos respecto a tolerancia'),
(2, 'LlegaTardeGrave', 'Demora mayor a 30 minutos'),
(3, 'SaleTempranoLeve', 'Retiro antes de hora entre 15 y 30 minutos'),
(4, 'SaleTempranoGrave', 'Retiro no autorizado con más de 30 minutos'),
(5, 'Ausencia', 'Inasistencia total injustificada a actividad obligatoria'),
(6, 'NoMarcoEntrada', 'Omitió registrar huella biométrica al ingreso'),
(7, 'NoMarcoSalida', 'Omitió registrar huella biométrica a la salida');

-- 7.20 Tipos de Justificación (Causales Tipificadas T02)
INSERT INTO `tribunal_justificacion` (`idJustificacion`, `nombre`, `descripcion`) VALUES
(1, 'Enfermedad', 'Certificado médico oficial homologado'),
(2, 'Laboral', 'Constancia patronal de horas extras o guardia'),
(3, 'Académico', 'Examen parcial/final en UTN o constancia de cursado'),
(4, 'Viaje', 'Pasaje o constancia de viaje acreditada'),
(5, 'Catástrofe', 'Fuerza mayor, anegamiento o siniestro'),
(6, 'Gobierno', 'Convocatoria judicial, electoral o estatal obligatoria'),
(7, 'Deceso', 'Fallecimiento de familiar directo'),
(8, 'Transporte', 'Paro de transporte público no programado');

-- 7.21 Catálogo de Valores de Sanción y Reconocimiento
INSERT INTO `tribunal_valorsancion` (`idSancion`, `nombre`, `valor`) VALUES
(1, 'Felicitación Formal', 0.33),
(2, 'Llamado de Atención', -0.33),
(3, 'Sanción Leve (-0.5)', -0.50),
(4, 'Falta Ordinaria (-1.0)', -1.00),
(5, 'Sanción Grave (-1.5)', -1.50),
(6, 'Sanción Gravísima (-2.0)', -2.00),
(7, 'Reconocimiento Destacado (+1.0)', 1.00);

-- 7.22 Artículos del Reglamento Interno
INSERT INTO `tribunal_reglamento` (`idReglamento`, `titulo`, `seccion`, `articulo`, `inciso`, `descripcion`) VALUES
(1, 'Reglamento Interno Disciplinario', 1, 12, 'a', 'Inasistencia no justificada a asambleas generales ordinarias y extraordinarias.'),
(2, 'Reglamento Interno Disciplinario', 1, 12, 'b', 'Impuntualidad reiterada en actividades oficiales de subcomisión.'),
(3, 'Reglamento Interno Disciplinario', 2, 25, '-', 'Incumplimiento de tareas asignadas en turnos de mantenimiento institucional.'),
(4, 'Reglamento Interno Disciplinario', 3, 40, 'c', 'Conducta contraria al espíritu de camaradería y decoro estatutario.');

-- 7.23 Tipos de Eventos Institucionales
INSERT INTO `tribunal_tipoevento` (`idTipoEvento`, `nombre`, `sancionFalta_id`, `sancionLeve_id`, `sancionGrave_id`) VALUES
(1, 'Asamblea General Ordinaria', 5, 3, 4),
(2, 'Reunión Quincenal de Socios', 4, 3, 4),
(3, 'Reunión Ordinaria de Subcomisión', 4, 2, 3),
(4, 'Jornada Integral de Limpieza', 5, 3, 4);

-- --------------------------------------------------------------------------------------
-- 8. DATOS DE PRUEBA / REGISTROS REPRESENTATIVOS (MOCK DATA SANITIZADO)
-- --------------------------------------------------------------------------------------

-- 8.1 Usuarios del Sistema (Login por NroSocio)
INSERT INTO `auth_user` (`id`, `password`, `is_superuser`, `username`, `first_name`, `last_name`, `email`, `is_staff`, `is_active`) VALUES
(1, 'pbkdf2_sha256$150000$dummyhash$mockpassword123', 1, '1001', 'Esteban', 'Pérez', 'esteban.perez@aveit.utn.edu.ar', 1, 1),
(2, 'pbkdf2_sha256$150000$dummyhash$mockpassword123', 0, '1002', 'Lucía', 'Gómez', 'lucia.gomez@aveit.utn.edu.ar', 0, 1),
(3, 'pbkdf2_sha256$150000$dummyhash$mockpassword123', 0, '1003', 'Martín', 'Rossi', 'martin.rossi@aveit.utn.edu.ar', 0, 1);

-- 8.2 Socios
INSERT INTO `socio_lista` (`nroSocio`, `apellido`, `nombre`, `fechaIngreso`, `codTipoDoc`, `nroDoc`, `fechaNac`, `codSexo`, `codSubcomision`, `codEstadoCivil`, `fechaBaja`, `anoSocial`, `ingresante`, `idTipoSocio`, `user_id`, `forzarCambioClave`) VALUES
(1001, 'Pérez', 'Esteban', '2021-03-15', 1, 41234567, '2000-05-10', 1, 10, 1, NULL, 4, 0, 10, 1, 0), -- Titular TD
(1002, 'Gómez', 'Lucía', '2022-03-20', 1, 42345678, '2001-08-22', 2, 1, 1, NULL, 3, 0, 1, 2, 0),   -- Presidente Cómputos
(1003, 'Rossi', 'Martín', '2023-04-01', 1, 43456789, '2002-11-15', 1, 1, 1, NULL, 2, 0, 12, 3, 0);  -- Socio Ordinario

-- 8.3 Historial de Estados de Socios
INSERT INTO `socio_estadoHistorial` (`idEstadoHistorial`, `idGrupo`, `nroSocio`, `fechaHora`, `codEstadoSocio`, `socio_motivoCambioEstado`) VALUES
(1, 54, 1001, '2021-03-15 10:00:00.000000', 1, 1),
(2, 55, 1002, '2022-03-20 11:30:00.000000', 1, 1),
(3, 56, 1003, '2023-04-01 09:15:00.000000', 1, 1);

-- 8.4 Estudios y Legajo Universitario
INSERT INTO `socio_estudio` (`compositeKey`, `nroSocio`, `nroLegajo`, `codEspecialidad`, `curso`, `aula`, `codTurno`) VALUES
(100101, 1001, 85421, 1, '5K1', 'Aula 12', 3),
(100201, 1002, 89123, 1, '4K2', 'Aula 15', 2),
(100301, 1003, 90455, 1, '3K3', 'Aula 08', 1);

-- 8.5 Correos y Teléfonos
INSERT INTO `socio_email` (`compositeKey`, `nroSocio`, `idEmail`, `email`, `comprobado`, `habilitado`) VALUES
(100100, 1001, 0, 'esteban.perez@aveit.utn.edu.ar', 1, 1),
(100200, 1002, 0, 'lucia.gomez@aveit.utn.edu.ar', 1, 1),
(100300, 1003, 0, 'martin.rossi@aveit.utn.edu.ar', 1, 1);

INSERT INTO `socio_telefono` (`compositeKey`, `nroSocio`, `idTelefono`, `telefono`, `codTipoTelefono`) VALUES
(100101, 1001, 0, '3515112233', 1),
(100201, 1002, 0, '3515223344', 1),
(100301, 1003, 0, '3515334455', 1);

-- 8.6 Evento Institucional y Asistencia
INSERT INTO `tribunal_evento` (`idEvento`, `nombre`, `afectados_id`, `fechaHoraInicio`, `fechaHoraFin`, `tieneHoraFin`, `responsable_id`, `estadoEvento_id`, `tipoEvento_id`, `sancionPersonalizada_id`, `toleranciaLeveMinutos`, `toleranciaGraveMinutos`) VALUES
(1, 'Asamblea Extraordinaria de Mayo', 20, '2024-05-10 19:00:00.000000', '2024-05-10 22:00:00.000000', 1, 1001, 4, 1, NULL, 15, 30);

INSERT INTO `tribunal_asistente` (`idAsistente`, `evento_id`, `socio_id`, `fechaHoraLlegada`, `fechaHoraSalida`, `notificado`, `fechaNotificacion`) VALUES
(1, 1, 1001, '2024-05-10 18:55:00.000000', '2024-05-10 22:05:00.000000', 0, NULL),
(2, 1, 1002, '2024-05-10 19:10:00.000000', '2024-05-10 22:00:00.000000', 0, NULL),
(3, 1, 1003, NULL, NULL, 1, '2024-05-11'); -- Inasistencia de Martín Rossi

-- 8.7 Solicitud T01
INSERT INTO `tribunal_solicitud` (`idSolicitud`, `fechaHora`, `titulo`, `motivoSancion`, `responsable_id`, `sancionSolicitada_id`, `reglamento`) VALUES
(1, '2024-05-12 14:00:00.000000', 'Inasistencia no informada a asamblea obligatoria', 'El socio no concurrió a la Asamblea ni envió previo aviso fundado.', 1002, 4, 'Art. 12 Inc. a R.I.');

-- 8.8 Considerandos y Vistos
INSERT INTO `tribunal_datosresolucion` (`idDatosResolucion`, `reglamento1`, `reglamento2`, `reglamento3`, `responsable1_id`, `responsable2_id`, `responsable3_id`, `responsable1Text`, `responsable2Text`, `responsable3Text`, `consideracion`) VALUES
(1, 'Art. 12 Inc. a Reglamento Interno Disciplinario', NULL, NULL, 1001, NULL, NULL, 'Esteban Pérez', NULL, NULL, 'VISTO la inasistencia constatada por lector biométrico en la Asamblea del 10/05/2024 y no habiéndose recibido justificación fehaciente en el plazo legal de cinco días.');

-- 8.9 Expediente Disciplinario
INSERT INTO `tribunal_expediente` (`idExpediente`, `nroExpediente`, `estadoExpediente_id`, `solicitud_id`, `evento_id`, `tipoSancion_id`, `fechaHora`, `puntos_id`, `dataRes_id`) VALUES
(1, '01/2024', 6, 1, 1, 5, '2024-05-13 10:00:00.000000', 4, 1);

-- 8.10 Sanción Individual Imputada
INSERT INTO `tribunal_sancion` (`idSancion`, `socio_id`, `expediente_id`, `estadoJustificacion_id`, `fechaLimiteEnvio`, `notificacionSancion`, `aprobada`, `responsable_id`) VALUES
(1, 1003, 1, 4, '2024-05-20 23:59:59.000000', 1, 1, 1001);

-- 8.11 Formulario T02 (Descargo Desaprobado)
INSERT INTO `tribunal_t02` (`idT02`, `justificacion_id`, `observacion`, `socio_id`, `sancion_id`, `fechaHora`, `justificativo`) VALUES
(1, 3, 'Examen de Física II que finalizó a las 20:30 hs, comprobante adjunto.', 1003, 1, '2024-05-18 16:30:00.000000', 'svaveit/tribunal/justificativos/t02_1003_exp1.pdf');

-- 8.12 Disposición Final Dictada
INSERT INTO `tribunal_disposicion` (`idDisposicion`, `nroDisposicion`, `expediente_id`, `fechaHora`, `estadoDisposicion_id`, `responsable1_id`, `responsable2_id`, `responsable3_id`, `responsable1Text`, `responsable2Text`, `responsable3Text`, `resolucion`, `reglamento`) VALUES
(1, '01/2024', 1, '2024-05-22 18:00:00.000000', 2, 1001, NULL, NULL, 'Esteban Pérez', NULL, NULL, 'RESUELVE: Art. 1: Desestimar el descargo presentado por resultar extemporáneo. Art. 2: Aplicar la sanción de 1 punto en contra al socio N° 1003.', 'Art. 12 Inc. a R.I.');

-- 8.13 Libro Mayor Transaccional de Puntos (PuntajeAplicado)
INSERT INTO `tribunal_puntajeaplicado` (`idPuntajeAplicado`, `puntajeAplicado`, `socio_id`, `expediente_id`) VALUES
(1, -1.0, 1003, 1);

-- 8.14 Caché de Puntaje General
INSERT INTO `tribunal_puntajegeneral` (`idPuntajeGeneral`, `socio_id`, `puntos`, `felicitaciones`, `llamadosAtencion`) VALUES
(1, 1001, 0, 1, 0),
(2, 1002, 0, 0, 0),
(3, 1003, -1.0, 0, 0);

SET FOREIGN_KEY_CHECKS = 1;

-- ======================================================================================
-- FIN DE SCRIPT: Esquema físico y catálogos levantados exitosamente.
-- ======================================================================================
