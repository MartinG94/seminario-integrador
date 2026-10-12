-- DDL mínimo de demostración SCRUM-77 (TS77.05/38), MySQL 8.0.
-- Fuente: docs/analisis-proceso-actual/sistema-actual/sistema_actual_legado_schema.sql
-- Incluye las 8 tablas unmanaged consumidas por padrón/ranking y su cierre de FKs.
-- auth_user es externo: debe existir mediante las migraciones reales de Django.
-- Adaptaciones: puntos y puntajeAplicado usan DECIMAL(10,2), conforme al ORM vigente.
-- Tercera adaptación demo: socio_lista.anoSocial nullable, sin año ficticio para exviajeros.
-- Sólo creación; sin datos, limpieza, cambio de base ni desactivación de FKs.
-- TS77.06 aplica y valida el contrato; transición de una demo anterior pendiente en TS77.39.
-- No ejecutar este archivo manualmente contra una base existente.

CREATE TABLE `socio_tipodocumento` (
  `codTipoDoc` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(45) NOT NULL,
  `descripcion` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`codTipoDoc`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `socio_sexo` (
  `codSexo` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(45) NOT NULL,
  `descripcion` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`codSexo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `socio_tiposubcomision` (
  `codSubcomision` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(45) NOT NULL,
  PRIMARY KEY (`codSubcomision`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `socio_estadocivil` (
  `codEstadoCivil` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(45) NOT NULL,
  `descripcion` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`codEstadoCivil`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `socio_tipoSocio` (
  `idTipoSocio` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(45) NOT NULL,
  PRIMARY KEY (`idTipoSocio`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `socio_estado` (
  `codEstadoSocio` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(45) NOT NULL,
  `descripcion` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`codEstadoSocio`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `socio_motivoCambioEstado` (
  `idMotivoCambio` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(45) NOT NULL,
  `descripcion` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`idMotivoCambio`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `socio_especialidad` (
  `codEspecialidad` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(45) NOT NULL,
  `descripcion` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`codEspecialidad`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `socio_tipoEstudioTurno` (
  `codTipoEstudioTurno` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(45) NOT NULL,
  `descripcion` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`codTipoEstudioTurno`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `grupo_lista` (
  `nroGrupo` int(11) NOT NULL,
  `nombre` varchar(45) NOT NULL,
  `descripcion` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`nroGrupo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

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
  `anoSocial` int(11) DEFAULT NULL,
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

CREATE TABLE `tribunal_afectados` (
  `idAfectados` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(30) NOT NULL,
  `descripcion` varchar(80) NOT NULL,
  PRIMARY KEY (`idAfectados`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `tribunal_estadoevento` (
  `idEstadoEvento` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(30) NOT NULL,
  `descripcion` varchar(80) NOT NULL,
  PRIMARY KEY (`idEstadoEvento`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `tribunal_estadoexpediente` (
  `idEstadoExpediente` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(30) NOT NULL,
  `descripcion` varchar(80) NOT NULL,
  PRIMARY KEY (`idEstadoExpediente`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `tribunal_tiposancion` (
  `idTipoSancion` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(30) NOT NULL,
  `descripcion` varchar(80) NOT NULL,
  PRIMARY KEY (`idTipoSancion`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `tribunal_valorsancion` (
  `idSancion` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(30) NOT NULL,
  `valor` double NOT NULL,
  PRIMARY KEY (`idSancion`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

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

CREATE TABLE `tribunal_puntajeaplicado` (
  `idPuntajeAplicado` int(11) NOT NULL AUTO_INCREMENT,
  `puntajeAplicado` decimal(10,2) NOT NULL,
  `socio_id` int(11) NOT NULL,
  `expediente_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`idPuntajeAplicado`),
  KEY `fk_ptjaplicado_socio` (`socio_id`),
  KEY `fk_ptjaplicado_expediente` (`expediente_id`),
  CONSTRAINT `fk_ptjaplicado_socio` FOREIGN KEY (`socio_id`) REFERENCES `socio_lista` (`nroSocio`),
  CONSTRAINT `fk_ptjaplicado_expediente` FOREIGN KEY (`expediente_id`) REFERENCES `tribunal_expediente` (`idExpediente`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `tribunal_puntajegeneral` (
  `idPuntajeGeneral` int(11) NOT NULL AUTO_INCREMENT,
  `socio_id` int(11) NOT NULL,
  `puntos` decimal(10,2) NOT NULL DEFAULT 0,
  `felicitaciones` int(11) NOT NULL DEFAULT 0,
  `llamadosAtencion` int(11) NOT NULL DEFAULT 0,
  PRIMARY KEY (`idPuntajeGeneral`),
  UNIQUE KEY `socio_id_unique` (`socio_id`),
  CONSTRAINT `fk_ptjgral_socio` FOREIGN KEY (`socio_id`) REFERENCES `socio_lista` (`nroSocio`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
