/*
 * GNATdashboard
 * Copyright (C) 2017, AdaCore
 *
 * This is free software;  you can redistribute it  and/or modify it  under
 * terms of the  GNU General Public License as published  by the Free Soft-
 * ware  Foundation;  either version 3,  or (at your option) any later ver-
 * sion.  This software is distributed in the hope  that it will be useful,
 * but WITHOUT ANY WARRANTY;  without even the implied warranty of MERCHAN-
 * TABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public
 * License for  more details.  You should have  received  a copy of the GNU
 * General  Public  License  distributed  with  this  software;   see  file
 * COPYING3.  If not, go to http://www.gnu.org/licenses for a complete copy
 * of the license.
 */

package org.sonar.plugins.ada.rules;

import lombok.AllArgsConstructor;
import lombok.Getter;
import org.sonar.api.batch.rule.Severity;

@AllArgsConstructor
public enum SPARK2014Severity {
  ERROR(Severity.BLOCKER),
  HIGH(Severity.CRITICAL),
  MEDIUM(Severity.MAJOR),
  LOW(Severity.MINOR),
  INFO(Severity.INFO);

  @Getter private final Severity sonarSeverity;
}
