package com.example.toy

import org.junit.Assert.assertEquals
import org.junit.Test

class MainActivityTest {
    @Test
    fun addReturnsSum() {
        val mainActivity = MainActivity()
        assertEquals(5, mainActivity.add(2, 3))
    }
}
