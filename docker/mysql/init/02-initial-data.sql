-- ======================================================================================
-- SGD-AVEIT — Padrón Institucional y Datos Iniciales de Producción / Desarrollo
-- Archivo: docker/mysql/init/02-initial-data.sql
-- Propósito: Esquema de sólo lectura legado (MySQL) y datos representativos
--            garantizando la existencia y elegibilidad de socios institucionales
--            y la consistencia estricta de saldos vs expedientes cerrados.
-- ======================================================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- --------------------------------------------------------------------------------------
-- 1. CATÁLOGOS BASE
-- --------------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS `socio_tipodocumento` (
  `codTipoDoc` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(45) NOT NULL,
  `descripcion` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`codTipoDoc`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `socio_tipodocumento` (`codTipoDoc`, `nombre`, `descripcion`) VALUES
(1, 'DNI', 'Documento Nacional de Identidad'),
(2, 'Pasaporte', 'Pasaporte Internacional'),
(3, 'LC', 'Libreta Cívica'),
(4, 'LE', 'Libreta de Enrolamiento')
ON DUPLICATE KEY UPDATE `nombre`=VALUES(`nombre`);

CREATE TABLE IF NOT EXISTS `socio_sexo` (
  `codSexo` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(45) NOT NULL,
  `descripcion` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`codSexo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `socio_sexo` (`codSexo`, `nombre`, `descripcion`) VALUES
(1, 'Masculino', 'Sexo Masculino'),
(2, 'Femenino', 'Sexo Femenino'),
(3, 'Otro', 'No binario / No especificado')
ON DUPLICATE KEY UPDATE `nombre`=VALUES(`nombre`);

CREATE TABLE IF NOT EXISTS `socio_estadocivil` (
  `codEstadoCivil` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(45) NOT NULL,
  `descripcion` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`codEstadoCivil`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `socio_estadocivil` (`codEstadoCivil`, `nombre`, `descripcion`) VALUES
(1, 'Soltero/a', 'Estado civil soltero'),
(2, 'Casado/a', 'Estado civil casado'),
(3, 'Divorciado/a', 'Estado civil divorciado'),
(4, 'Viudo/a', 'Estado civil viudo')
ON DUPLICATE KEY UPDATE `nombre`=VALUES(`nombre`);

CREATE TABLE IF NOT EXISTS `socio_tiposubcomision` (
  `codSubcomision` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(45) NOT NULL,
  PRIMARY KEY (`codSubcomision`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

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
(99, 'Sin Subcomisión')
ON DUPLICATE KEY UPDATE `nombre`=VALUES(`nombre`);

CREATE TABLE IF NOT EXISTS `socio_tipoSocio` (
  `idTipoSocio` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(45) NOT NULL,
  PRIMARY KEY (`idTipoSocio`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `socio_tipoSocio` (`idTipoSocio`, `nombre`) VALUES
(1, 'Socio Activo'),
(2, 'Socio Adherente'),
(3, 'Socio Vitalicio'),
(4, 'Socio Honorario'),
(10, 'Titular Tribunal Disciplina'),
(12, 'Socio Ordinario')
ON DUPLICATE KEY UPDATE `nombre`=VALUES(`nombre`);

CREATE TABLE IF NOT EXISTS `socio_estado` (
  `codEstadoSocio` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(45) NOT NULL,
  `descripcion` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`codEstadoSocio`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `socio_estado` (`codEstadoSocio`, `nombre`, `descripcion`) VALUES
(1, 'Habilitado', 'Socio activo con derechos plenos'),
(2, 'En receso', 'Socio en receso académico o temporal'),
(3, 'Sancionado', 'Socio con sanción disciplinaria vigente'),
(4, 'Suspendido', 'Membresía suspendida por falta de pago'),
(5, 'Baja', 'Socio dado de baja definitivamente')
ON DUPLICATE KEY UPDATE `nombre`=VALUES(`nombre`);

CREATE TABLE IF NOT EXISTS `socio_motivoCambioEstado` (
  `idMotivoCambio` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(45) NOT NULL,
  `descripcion` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`idMotivoCambio`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `socio_motivoCambioEstado` (`idMotivoCambio`, `nombre`, `descripcion`) VALUES
(1, 'Regular', 'Evolución societaria normal'),
(2, 'Solicitud propia', 'Petición formal del socio'),
(3, 'Resolución TD', 'Disposición del Tribunal de Disciplina'),
(4, 'Falta de pago', 'Incumplimiento de cuota social')
ON DUPLICATE KEY UPDATE `nombre`=VALUES(`nombre`);

CREATE TABLE IF NOT EXISTS `socio_especialidad` (
  `codEspecialidad` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(45) NOT NULL,
  `descripcion` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`codEspecialidad`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `socio_especialidad` (`codEspecialidad`, `nombre`, `descripcion`) VALUES
(1, 'Ingeniería en Sistemas de Información', 'Carrera de grado UTN FRC'),
(2, 'Ingeniería Electrónica', 'Carrera de grado UTN FRC'),
(3, 'Ingeniería Mecánica', 'Carrera de grado UTN FRC'),
(4, 'Ingeniería Industrial', 'Carrera de grado UTN FRC')
ON DUPLICATE KEY UPDATE `nombre`=VALUES(`nombre`);

CREATE TABLE IF NOT EXISTS `grupo_lista` (
  `nroGrupo` int(11) NOT NULL,
  `nombre` varchar(45) NOT NULL,
  `descripcion` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`nroGrupo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `grupo_lista` (`nroGrupo`, `nombre`, `descripcion`) VALUES
(54, 'G54', 'Grupo Histórico 54'),
(55, 'G55', 'Grupo Histórico 55'),
(56, 'G56', 'Grupo Histórico 56'),
(57, 'G57', 'Grupo 57 - Exviajeros'),
(58, 'G58', 'Grupo 58 - Senior 6to'),
(59, 'G59', 'Grupo 59 - Senior 5to'),
(60, 'G60', 'Grupo 60 - Senior 4to'),
(62, 'G62', 'Grupo 62 - Junior 2do'),
(63, 'G63', 'Grupo 63 - Junior 1ro')
ON DUPLICATE KEY UPDATE `nombre`=VALUES(`nombre`);

-- --------------------------------------------------------------------------------------
-- 2. TABLAS DEL PADRÓN INSTITUCIONAL
-- --------------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS `socio_lista` (
  `nroSocio` int(11) NOT NULL,
  `apellido` varchar(45) NOT NULL,
  `nombre` varchar(45) NOT NULL,
  `fechaIngreso` date NOT NULL,
  `codTipoDoc` int(11) NOT NULL,
  `nroDoc` int(11) NOT NULL,
  `fechaNac` date DEFAULT NULL,
  `codSexo` int(11) NOT NULL,
  `codSubcomision` int(11) DEFAULT NULL,
  `codEstadoCivil` int(11) DEFAULT NULL,
  `fechaBaja` date DEFAULT NULL,
  `anoSocial` int(11) DEFAULT NULL,
  `ingresante` tinyint(1) NOT NULL DEFAULT 0,
  `idTipoSocio` int(11) DEFAULT NULL,
  `user_id` int(11) DEFAULT NULL,
  `forzarCambioClave` tinyint(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`nroSocio`),
  KEY `fk_socio_subcomision` (`codSubcomision`),
  KEY `fk_socio_tipodoc` (`codTipoDoc`),
  KEY `fk_socio_sexo` (`codSexo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `socio_estudio` (
  `compositeKey` int(11) NOT NULL,
  `nroSocio` int(11) NOT NULL,
  `nroLegajo` int(11) NOT NULL,
  `codEspecialidad` int(11) NOT NULL,
  `curso` varchar(10) DEFAULT NULL,
  `aula` varchar(10) DEFAULT NULL,
  `codTurno` int(11) DEFAULT NULL,
  PRIMARY KEY (`compositeKey`),
  KEY `fk_estudio_socio` (`nroSocio`),
  KEY `idx_estudio_legajo` (`nroLegajo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `socio_email` (
  `compositeKey` int(11) NOT NULL,
  `nroSocio` int(11) NOT NULL,
  `idEmail` int(11) NOT NULL,
  `email` varchar(45) NOT NULL,
  `comprobado` tinyint(1) NOT NULL DEFAULT 0,
  `habilitado` tinyint(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`compositeKey`),
  KEY `fk_email_socio` (`nroSocio`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `socio_estadoHistorial` (
  `idEstadoHistorial` int(11) NOT NULL AUTO_INCREMENT,
  `idGrupo` int(11) NOT NULL,
  `nroSocio` int(11) NOT NULL,
  `fechaHora` datetime(6) NOT NULL,
  `codEstadoSocio` int(11) NOT NULL,
  `socio_motivoCambioEstado` int(11) NOT NULL,
  PRIMARY KEY (`idEstadoHistorial`),
  KEY `fk_historial_socio` (`nroSocio`),
  KEY `fk_historial_estado` (`codEstadoSocio`),
  KEY `idx_historial_fecha` (`fechaHora`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------------------------------------
-- 3. INSERCIÓN DE SOCIOS DE LOGIN Y EQUIPO
-- --------------------------------------------------------------------------------------

INSERT INTO `socio_lista` (`nroSocio`, `apellido`, `nombre`, `fechaIngreso`, `codTipoDoc`, `nroDoc`, `fechaNac`, `codSexo`, `codSubcomision`, `codEstadoCivil`, `fechaBaja`, `anoSocial`, `ingresante`, `idTipoSocio`, `user_id`, `forzarCambioClave`) VALUES
(74907, 'Gastiaburu', 'Lucas', '2023-03-01', 1, 39074907, '2001-04-10', 1, 1, 1, NULL, 2, 0, 12, NULL, 0),
(85194, 'Guillén', 'Lucas Martín', '2021-03-01', 1, 39085194, '2000-02-15', 1, 2, 1, NULL, 4, 0, 12, NULL, 0),
(87414, 'Sánchez', 'Diego Gabriel', '2020-03-01', 1, 39087414, '1999-09-18', 1, 9, 1, NULL, 5, 0, 12, NULL, 0),
(408917, 'Rosales', 'Nicolás', '2019-03-01', 1, 40408917, '1998-11-20', 1, 10, 1, NULL, 6, 0, 10, NULL, 0),
(403655, 'Villegas', 'Axel René', '2020-03-01', 1, 40403655, '1999-07-25', 1, 1, 1, NULL, 5, 0, 12, NULL, 0),
(409953, 'Urviola', 'Luis', '2021-03-01', 1, 40409953, '2000-12-05', 1, 1, 1, NULL, 4, 0, 12, NULL, 0),
(415327, 'Quiroz', 'Tomas Augusto', '2022-03-01', 1, 40415327, '2001-08-30', 1, 1, 1, NULL, 3, 0, 12, NULL, 0),
(1001, 'Pérez', 'Esteban', '2021-03-15', 1, 41234567, '2000-05-10', 1, 10, 1, NULL, 4, 0, 10, NULL, 0),
(1002, 'Gómez', 'Lucía', '2022-03-15', 1, 42345678, '2001-07-12', 2, 1, 1, NULL, 3, 0, 12, NULL, 0),
(1003, 'Rossi', 'Martín', '2023-03-15', 1, 43456789, '2002-11-23', 1, 1, 1, NULL, 2, 0, 12, NULL, 0)
ON DUPLICATE KEY UPDATE `apellido`=VALUES(`apellido`), `nombre`=VALUES(`nombre`), `codSubcomision`=VALUES(`codSubcomision`), `anoSocial`=VALUES(`anoSocial`);

INSERT INTO `socio_estudio` (`compositeKey`, `nroSocio`, `nroLegajo`, `codEspecialidad`, `curso`, `aula`, `codTurno`) VALUES
(7490701, 74907, 74907, 1, '2K1', 'Aula 05', 1),
(8519401, 85194, 85194, 1, '4K2', 'Aula 14', 2),
(8741401, 87414, 87414, 1, '5K1', 'Aula 12', 3),
(40891701, 408917, 408917, 1, '6K1', 'Aula 20', 3),
(40365501, 403655, 403655, 1, '5K2', 'Aula 11', 2),
(40995301, 409953, 409953, 1, '4K1', 'Aula 09', 1),
(41532701, 415327, 415327, 1, '3K3', 'Aula 08', 2),
(100101, 1001, 85421, 1, '5K1', 'Aula 12', 3),
(100201, 1002, 89123, 1, '4K1', 'Aula 09', 2),
(100301, 1003, 90455, 1, '3K1', 'Aula 06', 1)
ON DUPLICATE KEY UPDATE `nroLegajo`=VALUES(`nroLegajo`);

INSERT INTO `socio_email` (`compositeKey`, `nroSocio`, `idEmail`, `email`, `comprobado`, `habilitado`) VALUES
(7490700, 74907, 0, '74907@aveit.test', 1, 1),
(8519400, 85194, 0, '85194@aveit.test', 1, 1),
(8741400, 87414, 0, '87414@aveit.test', 1, 1),
(40891700, 408917, 0, '408917@aveit.test', 1, 1),
(40365500, 403655, 0, '403655@aveit.test', 1, 1),
(40995300, 409953, 0, '409953@aveit.test', 1, 1),
(41532700, 415327, 0, '415327@aveit.test', 1, 1),
(100100, 1001, 0, 'esteban.perez@aveit.utn.edu.ar', 1, 1),
(100200, 1002, 0, 'lucia.gomez@aveit.utn.edu.ar', 1, 1),
(100300, 1003, 0, 'martin.rossi@aveit.utn.edu.ar', 1, 1)
ON DUPLICATE KEY UPDATE `email`=VALUES(`email`), `habilitado`=1;

INSERT INTO `socio_estadoHistorial` (`idEstadoHistorial`, `idGrupo`, `nroSocio`, `fechaHora`, `codEstadoSocio`, `socio_motivoCambioEstado`) VALUES
(749071, 62, 74907, '2023-03-01 10:00:00.000000', 1, 1),
(851941, 60, 85194, '2021-03-01 10:00:00.000000', 1, 1),
(874141, 59, 87414, '2020-03-01 10:00:00.000000', 1, 1),
(4089171, 58, 408917, '2019-03-01 10:00:00.000000', 1, 1),
(4036551, 59, 403655, '2020-03-01 10:00:00.000000', 1, 1),
(4099531, 60, 409953, '2021-03-01 10:00:00.000000', 1, 1),
(4153271, 62, 415327, '2022-03-01 10:00:00.000000', 1, 1),
(10011, 58, 1001, '2021-03-15 10:00:00.000000', 1, 1),
(10021, 60, 1002, '2022-03-15 10:00:00.000000', 1, 1),
(10031, 62, 1003, '2023-03-15 10:00:00.000000', 1, 1)
ON DUPLICATE KEY UPDATE `codEstadoSocio`=1;

-- --------------------------------------------------------------------------------------
-- 4. INSERCIÓN DE LOS 20 SOCIOS SINTÉTICOS G57–G63
-- --------------------------------------------------------------------------------------

INSERT INTO `socio_lista` (`nroSocio`, `apellido`, `nombre`, `fechaIngreso`, `codTipoDoc`, `nroDoc`, `fechaNac`, `codSexo`, `codSubcomision`, `codEstadoCivil`, `fechaBaja`, `anoSocial`, `ingresante`, `idTipoSocio`, `user_id`, `forzarCambioClave`) VALUES
-- G57 (Exviajeros - anoSocial 0 fuera de escala)
(770001, 'Faro Demo', 'Ámbar', '2019-03-01', 1, 100077001, '1998-05-01', 3, 1, 1, NULL, 0, 0, 12, NULL, 0),
(770002, 'Bruma Demo', 'Bastián', '2019-03-01', 1, 100077002, '1998-05-02', 3, 2, 1, NULL, 0, 0, 12, NULL, 0),
(770003, 'Cumbre Demo', 'Cira', '2019-03-01', 1, 100077003, '1998-05-03', 3, 3, 1, NULL, 0, 0, 12, NULL, 0),
(770004, 'Duna Demo', 'Darío', '2019-03-01', 1, 100077004, '1998-05-04', 3, 1, 1, NULL, 0, 0, 12, NULL, 0),
-- G58 (Senior - 6to año)
(770005, 'Ensayo Demo', 'Elena', '2020-03-01', 1, 100077005, '1998-05-05', 3, 2, 1, NULL, 6, 0, 12, NULL, 0),
(770006, 'Fábula Demo', 'Félix', '2020-03-01', 1, 100077006, '1998-05-06', 3, 3, 1, NULL, 6, 0, 12, NULL, 0),
(770007, 'García de las Nubes de Ensayo', 'Galatea', '2020-03-01', 1, 100077007, '1998-05-07', 3, 1, 1, NULL, 6, 0, 12, NULL, 0),
(770008, 'Horizonte Demo', 'Héctor', '2020-03-01', 1, 100077008, '1998-05-08', 3, 2, 1, NULL, 6, 0, 12, NULL, 0),
-- G59 (Senior - 5to año)
(770009, 'Isla Demo', 'Irina', '2021-03-01', 1, 100077009, '1998-05-09', 3, 3, 1, NULL, 5, 0, 12, NULL, 0),
(770010, 'Jardín Demo', 'Julián', '2021-03-01', 1, 100077010, '1998-05-10', 3, 1, 1, NULL, 5, 0, 12, NULL, 0),
(770011, 'Kilómetro Demo', 'Kira', '2021-03-01', 1, 100077011, '1998-05-11', 3, 2, 1, NULL, 5, 0, 12, NULL, 0),
(770012, 'Lago Demo', 'León', '2021-03-01', 1, 100077012, '1998-05-12', 3, 3, 1, NULL, 5, 0, 12, NULL, 0),
-- G60 (Senior - 4to año)
(770013, 'Marea Demo', 'Malena', '2022-03-01', 1, 100077013, '1998-05-13', 3, 1, 1, NULL, 4, 0, 12, NULL, 0),
(770014, 'Niebla Demo', 'Nereo', '2022-03-01', 1, 100077014, '1998-05-14', 3, 2, 1, NULL, 4, 0, 12, NULL, 0),
(770015, 'Orilla Demo', 'Ópalo', '2022-03-01', 1, 100077015, '1998-05-15', 3, 3, 1, NULL, 4, 0, 12, NULL, 0),
(770016, 'Puente Demo', 'Paz', '2022-03-01', 1, 100077016, '1998-05-16', 3, 99, 1, NULL, 4, 0, 12, NULL, 0),
-- G62 (Junior - 2do año)
(770017, 'Quimera Demo', 'Quimey', '2024-03-01', 1, 100077017, '1998-05-17', 3, 1, 1, NULL, 2, 0, 12, NULL, 0),
(770018, 'Rumbo Demo', 'Rocío', '2024-03-01', 1, 100077018, '1998-05-18', 3, 2, 1, NULL, 2, 0, 12, NULL, 0),
-- G63 (Junior - 1er año)
(770019, 'Sendero Demo', 'Sol', '2025-03-01', 1, 100077019, '1998-05-19', 3, 3, 1, NULL, 1, 0, 12, NULL, 0),
(770020, 'Trama Demo', 'Tomás', '2025-03-01', 1, 100077020, '1998-05-20', 3, 1, 1, NULL, 1, 0, 12, NULL, 0)
ON DUPLICATE KEY UPDATE `apellido`=VALUES(`apellido`), `nombre`=VALUES(`nombre`), `anoSocial`=VALUES(`anoSocial`);

INSERT INTO `socio_estudio` (`compositeKey`, `nroSocio`, `nroLegajo`, `codEspecialidad`, `curso`, `aula`, `codTurno`) VALUES
(1770001, 770001, 770001, 1, '5K1', 'Aula 12', 1),
(1770002, 770002, 770002, 1, '5K1', 'Aula 12', 1),
(1770003, 770003, 770003, 1, '5K1', 'Aula 12', 1),
(1770004, 770004, 770004, 1, '5K1', 'Aula 12', 1),
(1770005, 770005, 770005, 1, '6K1', 'Aula 20', 2),
(1770006, 770006, 770006, 1, '6K1', 'Aula 20', 2),
(1770007, 770007, 770007, 1, '6K1', 'Aula 20', 2),
(1770008, 770008, 770008, 1, '6K1', 'Aula 20', 2),
(1770009, 770009, 770009, 1, '5K2', 'Aula 15', 3),
(1770010, 770010, 770010, 1, '5K2', 'Aula 15', 3),
(1770011, 770011, 770011, 1, '5K2', 'Aula 15', 3),
(1770012, 770012, 770012, 1, '5K2', 'Aula 15', 3),
(1770013, 770013, 770013, 1, '4K1', 'Aula 09', 1),
(1770014, 770014, 770014, 1, '4K1', 'Aula 09', 1),
(1770015, 770015, 770015, 1, '4K1', 'Aula 09', 1),
(1770016, 770016, 770016, 1, '4K1', 'Aula 09', 1),
(1770017, 770017, 770017, 1, '2K1', 'Aula 05', 2),
(1770018, 770018, 770018, 1, '2K1', 'Aula 05', 2),
(1770019, 770019, 770019, 1, '1K1', 'Aula 02', 1),
(1770020, 770020, 770020, 1, '1K1', 'Aula 02', 1)
ON DUPLICATE KEY UPDATE `nroLegajo`=VALUES(`nroLegajo`);

INSERT INTO `socio_email` (`compositeKey`, `nroSocio`, `idEmail`, `email`, `comprobado`, `habilitado`) VALUES
(2770001, 770001, 1, 'g57.01@scrum77.test', 1, 1),
(2770002, 770002, 1, 'g57.02@scrum77.test', 1, 1),
(2770003, 770003, 1, 'g57.03@scrum77.test', 1, 1),
(2770004, 770004, 1, 'g57.04@scrum77.test', 1, 1),
(2770005, 770005, 1, 'g58.01@scrum77.test', 1, 1),
(2770006, 770006, 1, 'g58.02@scrum77.test', 1, 1),
(2770007, 770007, 1, 'g58.03@scrum77.test', 1, 1),
(2770008, 770008, 1, 'g58.04@scrum77.test', 1, 1),
(2770009, 770009, 1, 'g59.01@scrum77.test', 1, 1),
(2770010, 770010, 1, 'g59.02@scrum77.test', 1, 1),
(2770011, 770011, 1, 'g59.03@scrum77.test', 1, 1),
(2770012, 770012, 1, 'g59.04@scrum77.test', 1, 1),
(2770013, 770013, 1, 'g60.01@scrum77.test', 1, 1),
(2770014, 770014, 1, 'g60.02@scrum77.test', 1, 1),
(2770015, 770015, 1, 'g60.03@scrum77.test', 1, 1),
(2770016, 770016, 1, 'g60.04@scrum77.test', 1, 1),
(2770017, 770017, 1, 'g62.01@scrum77.test', 1, 1),
(2770018, 770018, 1, 'g62.02@scrum77.test', 1, 1),
(2770019, 770019, 1, 'g63.01@scrum77.test', 1, 1),
(2770020, 770020, 1, 'g63.02@scrum77.test', 1, 1)
ON DUPLICATE KEY UPDATE `email`=VALUES(`email`), `habilitado`=1;

INSERT INTO `socio_estadoHistorial` (`idEstadoHistorial`, `idGrupo`, `nroSocio`, `fechaHora`, `codEstadoSocio`, `socio_motivoCambioEstado`) VALUES
(7700011, 57, 770001, '2019-03-01 10:00:00.000000', 1, 1),
(7700021, 57, 770002, '2019-03-01 10:00:00.000000', 1, 1),
(7700031, 57, 770003, '2019-03-01 10:00:00.000000', 1, 1),
(7700041, 57, 770004, '2019-03-01 10:00:00.000000', 1, 1),
(7700051, 58, 770005, '2020-03-01 10:00:00.000000', 1, 1),
(7700061, 58, 770006, '2020-03-01 10:00:00.000000', 1, 1),
(7700071, 58, 770007, '2020-03-01 10:00:00.000000', 1, 1),
(7700081, 58, 770008, '2020-03-01 10:00:00.000000', 1, 1),
(7700091, 59, 770009, '2021-03-01 10:00:00.000000', 1, 1),
(7700101, 59, 770010, '2021-03-01 10:00:00.000000', 1, 1),
(7700111, 59, 770011, '2021-03-01 10:00:00.000000', 1, 1),
(7700121, 59, 770012, '2021-03-01 10:00:00.000000', 1, 1),
(7700131, 60, 770013, '2022-03-01 10:00:00.000000', 1, 1),
(7700141, 60, 770014, '2022-03-01 10:00:00.000000', 1, 1),
(7700151, 60, 770015, '2022-03-01 10:00:00.000000', 1, 1),
(7700161, 60, 770016, '2022-03-01 10:00:00.000000', 1, 1),
(7700171, 62, 770017, '2024-03-01 10:00:00.000000', 1, 1),
(7700181, 62, 770018, '2024-03-01 10:00:00.000000', 1, 1),
(7700191, 63, 770019, '2025-03-01 10:00:00.000000', 1, 1),
(7700201, 63, 770020, '2025-03-01 10:00:00.000000', 1, 1)
ON DUPLICATE KEY UPDATE `codEstadoSocio`=VALUES(`codEstadoSocio`);

-- --------------------------------------------------------------------------------------
-- 5. LIBRO MAYOR Y CACHÉ DE PUNTOS (CONSISTENCIA 100% RECONCILIADA)
-- --------------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS `tribunal_valorsancion` (
  `idSancion` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(45) NOT NULL,
  `valor` decimal(5,2) NOT NULL,
  PRIMARY KEY (`idSancion`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `tribunal_valorsancion` (`idSancion`, `nombre`, `valor`) VALUES
(1, 'Amonestación', 0.00),
(2, 'Leve', -1.00),
(3, 'Media', -2.00),
(4, 'Grave', -3.00)
ON DUPLICATE KEY UPDATE `valor`=VALUES(`valor`);

CREATE TABLE IF NOT EXISTS `tribunal_expediente` (
  `idExpediente` int(11) NOT NULL AUTO_INCREMENT,
  `nroExpediente` varchar(9) NOT NULL,
  `estadoExpediente_id` int(11) DEFAULT NULL,
  `solicitud_id` int(11) DEFAULT NULL,
  `evento_id` int(11) DEFAULT NULL,
  `tipoSancion_id` int(11) DEFAULT NULL,
  `fechaHora` datetime(6) DEFAULT CURRENT_TIMESTAMP(6),
  `puntos_id` int(11) NOT NULL DEFAULT 4,
  `dataRes_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`idExpediente`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `tribunal_expediente` (`idExpediente`, `nroExpediente`, `estadoExpediente_id`, `puntos_id`) VALUES
(1, '01/2026', 6, 2),
(2, '02/2026', 6, 2),
(5, '05/2026', 6, 4),
(6, '06/2026', 6, 3),
(8, '08/2026', 6, 2)
ON DUPLICATE KEY UPDATE `estadoExpediente_id`=VALUES(`estadoExpediente_id`);

CREATE TABLE IF NOT EXISTS `tribunal_puntajeaplicado` (
  `idPuntajeAplicado` int(11) NOT NULL AUTO_INCREMENT,
  `puntajeAplicado` decimal(10,2) NOT NULL,
  `socio_id` int(11) NOT NULL,
  `expediente_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`idPuntajeAplicado`),
  KEY `fk_puntaje_socio` (`socio_id`),
  KEY `idx_puntaje_expediente` (`expediente_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `tribunal_puntajegeneral` (
  `idPuntajeGeneral` int(11) NOT NULL AUTO_INCREMENT,
  `puntos` decimal(10,2) NOT NULL DEFAULT 0.00,
  `felicitaciones` int(11) NOT NULL DEFAULT 0,
  `llamadosAtencion` int(11) NOT NULL DEFAULT 0,
  `socio_id` int(11) NOT NULL,
  PRIMARY KEY (`idPuntajeGeneral`),
  UNIQUE KEY `idx_pg_socio` (`socio_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Asientos vinculados a expedientes históricos sintéticos
INSERT INTO `tribunal_puntajeaplicado` (`idPuntajeAplicado`, `puntajeAplicado`, `socio_id`, `expediente_id`) VALUES
(3,  3.00, 770005, 5), -- Elena Ensayo (G58): Mérito +3.00 (EXP-2026-005)
(4, -2.00, 770013, 6)  -- Malena Marea (G60): Sanción -2.00 (EXP-2026-006)
ON DUPLICATE KEY UPDATE `puntajeAplicado`=VALUES(`puntajeAplicado`), `socio_id`=VALUES(`socio_id`), `expediente_id`=VALUES(`expediente_id`);

-- Caché general estrictamente coincidente con la suma del libro mayor
INSERT INTO `tribunal_puntajegeneral` (`socio_id`, `puntos`, `felicitaciones`, `llamadosAtencion`) VALUES
(74907,  1.00, 1, 1), -- -1.00 + 2.00 = 1.00 pts (1 felicitación, 1 llamado)
(85194,  0.00, 0, 0), -- Sin sanciones emitidas
(87414,  1.00, 1, 0), -- +1.00 pt (1 felicitación)
(408917, 0.00, 0, 0), -- Sin sanciones emitidas
(403655, 0.00, 0, 0), -- Sin sanciones emitidas
(409953, 0.00, 0, 0), -- Sin sanciones emitidas
(415327, 0.00, 0, 0), -- Sin sanciones emitidas
(1001,   0.00, 0, 0), -- Sin sanciones emitidas
(1002,   0.00, 0, 0), -- Sin sanciones emitidas
(1003,   0.00, 0, 0), -- Sin sanciones emitidas
(770005, 3.00, 1, 0), -- +3.00 pts (1 felicitación)
(770013,-2.00, 0, 1)  -- -2.00 pts (1 llamado)
ON DUPLICATE KEY UPDATE `puntos`=VALUES(`puntos`), `felicitaciones`=VALUES(`felicitaciones`), `llamadosAtencion`=VALUES(`llamadosAtencion`);

-- --------------------------------------------------------------------------------------
-- 6. EVENTOS INSTITUCIONALES, ASISTENCIAS Y APERCIBIMIENTOS (SPEC 005 / SCRUM-50)
-- --------------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS `expedientes_evento` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `titulo` varchar(200) NOT NULL,
  `descripcion` longtext NOT NULL,
  `categoria` varchar(20) NOT NULL,
  `tipo` varchar(30) NOT NULL,
  `modalidad` varchar(30) NOT NULL DEFAULT 'PRESENCIAL_SEDE',
  `ubicacion` varchar(255) DEFAULT NULL,
  `lugar` varchar(200) NOT NULL DEFAULT 'Sede Central AVEIT',
  `fecha_publicacion` datetime(6) NOT NULL,
  `fecha_programada` datetime(6) NOT NULL,
  `fecha_fin` datetime(6) DEFAULT NULL,
  `fecha_hora_cierre_efectivo` datetime(6) DEFAULT NULL,
  `fecha_reporte` datetime(6) DEFAULT NULL,
  `tolerancia_tardanza_minutos` smallint(5) unsigned NOT NULL DEFAULT 15,
  `tolerancia_retiro_minutos` smallint(5) unsigned NOT NULL DEFAULT 15,
  `estado` varchar(30) NOT NULL DEFAULT 'PROGRAMADA',
  `modo_convocatoria` varchar(30) NOT NULL DEFAULT 'PERSONALIZADA',
  `grupo_convocado` varchar(10) DEFAULT NULL,
  `es_obligatoria` tinyint(1) NOT NULL DEFAULT 1,
  `es_sancionable` tinyint(1) NOT NULL DEFAULT 0,
  `motivo_no_sancionable` longtext DEFAULT NULL,
  `convocante_id` bigint(20) NOT NULL,
  `reportado_por_id` bigint(20) DEFAULT NULL,
  `subcomision_id` bigint(20) DEFAULT NULL,
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  KEY `idx_evento_fecha_prog_estado` (`fecha_programada`, `estado`),
  KEY `idx_evento_cat_tipo_sanc` (`categoria`, `tipo`, `es_sancionable`),
  KEY `fk_evento_convocante` (`convocante_id`),
  KEY `fk_evento_subcomision` (`subcomision_id`),
  KEY `fk_evento_reportado` (`reportado_por_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `expedientes_asistencia_evento` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `evento_id` bigint(20) NOT NULL,
  `socio_id` bigint(20) NOT NULL,
  `estado_asistencia` varchar(30) NOT NULL,
  `hora_registro` datetime(6) DEFAULT NULL,
  `hora_salida` datetime(6) DEFAULT NULL,
  `minutos_tardanza` int(10) unsigned NOT NULL DEFAULT 0,
  `minutos_retiro_anticipado` int(10) unsigned NOT NULL DEFAULT 0,
  `metodo_captura` varchar(20) NOT NULL DEFAULT 'MANUAL',
  `dispositivo_id` varchar(100) DEFAULT NULL,
  `motivo` longtext NOT NULL,
  `observaciones` longtext NOT NULL,
  `procesado_disciplinario` tinyint(1) NOT NULL DEFAULT 0,
  `expediente_generado_id` bigint(20) DEFAULT NULL,
  `apercibimiento_generado_id` bigint(20) DEFAULT NULL,
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_asistencia_per_evento_socio` (`evento_id`, `socio_id`),
  KEY `fk_asist_evento` (`evento_id`),
  KEY `fk_asist_socio` (`socio_id`),
  KEY `fk_asist_expediente` (`expediente_generado_id`),
  KEY `fk_asist_apercibimiento` (`apercibimiento_generado_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `expedientes_registro_apercibimiento` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `socio_id` bigint(20) NOT NULL,
  `origen_tipo` varchar(50) NOT NULL,
  `asistencia_id` bigint(20) DEFAULT NULL,
  `expediente_origen_id` bigint(20) DEFAULT NULL,
  `solicitud_t01_id` char(32) DEFAULT NULL,
  `fecha_hecho` date NOT NULL,
  `motivo` longtext NOT NULL,
  `articulo_reglamento` varchar(50) NOT NULL DEFAULT 'Art. 83',
  `estado` varchar(20) NOT NULL DEFAULT 'PENDIENTE',
  `lote_consolidacion` char(32) DEFAULT NULL,
  `expediente_sancion_id` bigint(20) DEFAULT NULL,
  `fecha_consolidacion` datetime(6) DEFAULT NULL,
  `actor_registro` varchar(150) NOT NULL DEFAULT 'SISTEMA',
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  KEY `idx_aperc_socio_est_created` (`socio_id`, `estado`, `created_at`),
  KEY `fk_aperc_socio` (`socio_id`),
  KEY `fk_aperc_asistencia` (`asistencia_id`),
  KEY `fk_aperc_exp_origen` (`expediente_origen_id`),
  KEY `fk_aperc_exp_sancion` (`expediente_sancion_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE OR REPLACE VIEW `expedientes_evento_institucional` AS SELECT * FROM `expedientes_evento`;

SET FOREIGN_KEY_CHECKS = 1;

