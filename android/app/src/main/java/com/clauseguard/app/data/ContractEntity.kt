package com.clauseguard.app.data

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "contracts")
data class ContractEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val title: String,
    val date: Long = System.currentTimeMillis(),
    val riskScore: Int,
    val rawText: String,
    val summaryJson: String
)