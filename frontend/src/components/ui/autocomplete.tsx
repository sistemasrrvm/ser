/**
 * Autocomplete Component
 * Campo de busca com dropdown de sugestões
 */

import { useState, useRef, useEffect, useCallback } from 'react'
import { Input } from './input'

export interface AutocompleteOption {
  label: string
  value: any
}

interface AutocompleteProps {
  options: AutocompleteOption[]
  value?: any
  /** Label do valor selecionado (usado quando options ainda não foram carregadas) */
  selectedLabel?: string
  inputId?: string
  onChange: (value: any) => void
  placeholder?: string
  disabled?: boolean
  maxResults?: number
  totalCount?: number
  minCharsForSearch?: number
  onSearch?: (searchTerm: string) => void
  onFocus?: () => void
}

const valuesMatch = (a: unknown, b: unknown) => String(a) === String(b)

export function Autocomplete({
  options,
  value,
  selectedLabel,
  inputId,
  onChange,
  placeholder = 'Digite para buscar...',
  disabled = false,
  maxResults = 50,
  totalCount = 0,
  minCharsForSearch = 0,
  onSearch,
  onFocus,
}: AutocompleteProps) {
  const [inputValue, setInputValue] = useState('')
  const [isOpen, setIsOpen] = useState(false)
  const [filteredOptions, setFilteredOptions] = useState<AutocompleteOption[]>([])
  const [highlightedIndex, setHighlightedIndex] = useState(-1)
  const wrapperRef = useRef<HTMLDivElement>(null)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const searchTimerRef = useRef<NodeJS.Timeout | null>(null)
  const lastSearchRef = useRef<string>('')

  // Determinar se precisa de busca mínima
  const requiresMinChars = minCharsForSearch > 0 && totalCount > 50
  const hasMinChars = inputValue.trim().length >= minCharsForSearch

  // Exibir label do valor selecionado (options carregadas ou selectedLabel do pai)
  useEffect(() => {
    if (!value) {
      if (inputValue !== '') setInputValue('')
      return
    }
    const fromOptions = options.find((opt) => valuesMatch(opt.value, value))
    const label = fromOptions?.label || selectedLabel
    if (label && inputValue !== label) {
      setInputValue(label)
    }
  }, [value, options, selectedLabel])

  // Filtrar opções quando input mudar
  useEffect(() => {
    // Se requer mínimo de caracteres e não atingiu, não filtrar
    if (requiresMinChars && !hasMinChars) {
      setFilteredOptions([])
      return
    }

    // Filtro local
    if (inputValue.trim() === '') {
      setFilteredOptions(options.slice(0, maxResults))
    } else {
      const searchTerm = inputValue.toLowerCase()
      const filtered = options
        .filter((opt) => opt.label.toLowerCase().includes(searchTerm))
        .slice(0, maxResults)
      setFilteredOptions(filtered)
    }
    setHighlightedIndex(-1)
  }, [inputValue, options, maxResults, requiresMinChars, hasMinChars])

  // Disparar busca no backend separadamente (com debounce e prevenção de loop)
  useEffect(() => {
    const searchTerm = inputValue.trim()

    // Prevenir buscas duplicadas
    if (lastSearchRef.current === searchTerm) {
      return
    }

    if (onSearch && searchTerm !== '' && hasMinChars && requiresMinChars) {
      // Limpar timer anterior
      if (searchTimerRef.current) {
        clearTimeout(searchTimerRef.current)
      }

      searchTimerRef.current = setTimeout(() => {
        lastSearchRef.current = searchTerm
        onSearch(searchTerm)
      }, 500) // Debounce de 500ms

      return () => {
        if (searchTimerRef.current) {
          clearTimeout(searchTimerRef.current)
        }
      }
    }
  }, [inputValue, hasMinChars, requiresMinChars])

  // Fechar dropdown ao clicar fora
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value
    setInputValue(newValue)
    setIsOpen(true)

    // Se limpar o input, limpar a seleção e resetar histórico de busca
    if (newValue === '') {
      onChange('')
      lastSearchRef.current = '' // Permitir nova busca após limpar
    }
  }

  const handleSelectOption = (option: AutocompleteOption) => {
    setInputValue(option.label)
    onChange(option.value)
    setIsOpen(false)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen) {
      if (e.key === 'ArrowDown' || e.key === 'Enter') {
        setIsOpen(true)
      }
      return
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        setHighlightedIndex((prev) =>
          prev < filteredOptions.length - 1 ? prev + 1 : prev
        )
        break
      case 'ArrowUp':
        e.preventDefault()
        setHighlightedIndex((prev) => (prev > 0 ? prev - 1 : 0))
        break
      case 'Enter':
        e.preventDefault()
        if (highlightedIndex >= 0 && highlightedIndex < filteredOptions.length) {
          handleSelectOption(filteredOptions[highlightedIndex])
        }
        break
      case 'Escape':
        setIsOpen(false)
        setHighlightedIndex(-1)
        break
    }
  }

  // Scroll automático para item highlighted
  useEffect(() => {
    if (highlightedIndex >= 0 && dropdownRef.current) {
      const highlightedElement = dropdownRef.current.children[highlightedIndex] as HTMLElement
      if (highlightedElement) {
        highlightedElement.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
      }
    }
  }, [highlightedIndex])

  return (
    <div ref={wrapperRef} className="relative">
      <Input
        id={inputId}
        type="text"
        value={inputValue}
        onChange={handleInputChange}
        onFocus={() => {
          setIsOpen(true)
          if (onFocus) onFocus()
        }}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={disabled}
        autoComplete="off"
      />

      {isOpen && filteredOptions.length > 0 && (
        <div
          ref={dropdownRef}
          className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto"
        >
          {filteredOptions.map((option, index) => (
            <div
              key={`${option.value}-${index}`}
              className={`px-3 py-2 cursor-pointer text-sm ${
                index === highlightedIndex
                  ? 'bg-blue-100 text-blue-900'
                  : 'hover:bg-gray-100'
              }`}
              onClick={() => handleSelectOption(option)}
              onMouseEnter={() => setHighlightedIndex(index)}
            >
              {option.label}
            </div>
          ))}
        </div>
      )}

      {isOpen && filteredOptions.length === 0 && inputValue.trim() !== '' && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg p-3 text-sm text-gray-500">
          {requiresMinChars && !hasMinChars ? (
            <div>
              <p className="font-semibold text-orange-600">Digite pelo menos {minCharsForSearch} caracteres</p>
              <p className="text-xs mt-1">Esta lista contém {totalCount} itens. Para melhor performance, digite alguns caracteres para filtrar.</p>
            </div>
          ) : (
            'Nenhum resultado encontrado'
          )}
        </div>
      )}

      {isOpen && inputValue.trim() === '' && requiresMinChars && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg p-3 text-sm">
          <p className="text-orange-600 font-semibold">📝 Digite pelo menos {minCharsForSearch} caracteres</p>
          <p className="text-gray-500 text-xs mt-1">
            Esta lista contém <strong>{totalCount} itens</strong>. Para melhor performance, digite alguns caracteres para buscar.
          </p>
        </div>
      )}
    </div>
  )
}
